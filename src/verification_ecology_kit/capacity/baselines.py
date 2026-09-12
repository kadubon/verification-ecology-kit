"""Matched finite FIFO/EDF/catalogue-order baselines using the same safety checker."""

from __future__ import annotations

from typing import Any

from verification_ecology_kit.capacity.checker import Snapshot, check_schedule
from verification_ecology_kit.capacity.model import Contract
from verification_ecology_kit.capacity.selector import plan


def compare(c: Contract, s: Snapshot) -> dict[str, Any]:
    works = {w.work_id: w for w in c.work}
    results: dict[str, Any] = {"exact": plan(c, s)}
    for name in ("default-order", "fifo", "earliest-deadline"):
        actions = list(c.actions)
        if name == "fifo":
            actions.sort(key=lambda a: (works[a.work_id].arrival, a.action_id))
        elif name == "earliest-deadline":
            actions.sort(key=lambda a: (works[a.work_id].deadline, a.action_id))
        schedule: dict[str, int] = {}
        examined = 0
        for action in actions:
            for start in range(s.clock, c.horizon):
                if examined >= c.max_candidates:
                    break
                examined += 1
                candidate = schedule | {action.action_id: start}
                try:
                    check_schedule(c, s, candidate)
                except ValueError:
                    continue
                schedule = candidate
                break
        results[name] = {
            "schedule": schedule,
            "checked": check_schedule(c, s, schedule).to_dict(),
            "examined": examined,
            "budget": c.max_candidates,
            "non_claim": "ordering heuristic; not an optimality certificate",
        }
    return results
