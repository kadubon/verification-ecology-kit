"""Bounded exhaustive reference allocation over a registered finite catalogue."""

from __future__ import annotations

from itertools import product
from math import prod
from typing import Any

from verification_ecology_kit.capacity.checker import Snapshot, check_schedule
from verification_ecology_kit.capacity.model import Contract


def plan(c: Contract, s: Snapshot) -> dict[str, Any]:
    options = []
    for a in c.actions:
        w = next(w for w in c.work if w.work_id == a.work_id)
        options.append(
            [-1]
            if (
                a.action_id in s.reservations
                or w.work_id in s.completed
                or w.work_id in s.cancelled
            )
            else [-1, *range(max(w.arrival, s.clock), c.horizon - a.duration + 1)]
        )
    total = prod(map(len, options))
    best = check_schedule(c, s, {})
    chosen: dict[str, int] = {}
    examined = valid = 0
    rejections: dict[str, int] = {}
    for assignment in product(*options):
        if examined >= c.max_candidates:
            break
        examined += 1
        schedule = {a.action_id: t for a, t in zip(c.actions, assignment, strict=True) if t >= 0}
        try:
            checked = check_schedule(c, s, schedule)
        except ValueError as exc:
            reason = str(exc)
            rejections[reason] = rejections.get(reason, 0) + 1
            continue
        valid += 1
        if checked.objective > best.objective or (
            checked.objective == best.objective
            and tuple(sorted(schedule.items())) < tuple(sorted(chosen.items()))
        ):
            best, chosen = checked, schedule
    complete = examined == total
    return {
        "contract_digest": c.contract_digest,
        "source_digest": s.source_digest,
        "revision": s.revision,
        "schedule": chosen,
        "checked": best.to_dict(),
        "search": {
            "complete": complete,
            "candidates": total,
            "examined": examined,
            "valid": valid,
            "budget": c.max_candidates,
            "checker_calls": examined + 1,
            "rejections": rejections,
            "status": "feasible" if best.mandatory_met else "infeasible" if complete else "unknown",
            "optimality": "finite-catalogue" if complete else "checked-incumbent",
        },
    }
