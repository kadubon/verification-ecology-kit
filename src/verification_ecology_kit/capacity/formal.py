"""Accounting projection of actual reducer transitions; independent numeric evaluator."""

from __future__ import annotations

from typing import Any

from verification_ecology_kit.capacity.checker import Snapshot
from verification_ecology_kit.capacity.model import Contract, require
from verification_ecology_kit.capacity.reducer import replay


def project(c: Contract, s: Snapshot, coordinate: int) -> dict[str, int]:
    r = c.resources[coordinate]
    reserved = sum(
        a.costs[coordinate] * (a.duration if r.kind == "pool" else 1)
        for a in c.actions
        if a.action_id in s.reservations
    )
    return {
        "unfinished": len(c.work) - len(s.completed),
        "completed": len(s.completed),
        "available": sum(r.capacity) - s.spent[coordinate] - reserved,
        "reserved": reserved,
        "consumed": s.spent[coordinate],
        "authority": 0,
    }


def trace(c: Contract, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    previous = replay(c, [])
    for i, event in enumerate(events):
        current = replay(c, events[: i + 1])
        for coordinate in range(len(c.resources)):
            before, after = project(c, previous, coordinate), project(c, current, coordinate)
            row = {
                "event": event["kind"],
                "coordinate": coordinate,
                "before": before,
                "after": after,
                "source_residuals": [w.residual_id for w in c.work],
            }
            evaluate(row)
            rows.append(row)
        previous = current
    return rows


def evaluate(row: dict[str, Any]) -> None:
    """Independent conservation check; no reducer or scheduler call."""
    before, after = row["before"], row["after"]
    require(
        all(type(x) is int and x >= 0 for x in [*before.values(), *after.values()]),
        "negative/noninteger formal quantity",
    )
    require(
        before["unfinished"] + before["completed"] == after["unfinished"] + after["completed"],
        "work conservation failure",
    )
    require(
        sum(before[x] for x in ("available", "reserved", "consumed"))
        == sum(after[x] for x in ("available", "reserved", "consumed")),
        "resource conservation failure",
    )
    require(before["authority"] == after["authority"], "authority inflation")
    require(
        after["completed"] >= before["completed"] and after["consumed"] >= before["consumed"],
        "history erased",
    )
    if row["event"] != "result":
        require(after["completed"] == before["completed"], "planning credited completion")
