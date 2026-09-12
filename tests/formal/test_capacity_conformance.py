"""Actual runtime/reducer projections and negative accounting traces."""

from copy import deepcopy

import pytest

from verification_ecology_kit.capacity.examples import scenario
from verification_ecology_kit.capacity.formal import evaluate, trace
from verification_ecology_kit.capacity.reducer import synthetic_result
from verification_ecology_kit.capacity.runtime import CapacityRuntime
from verification_ecology_kit.runtime.in_memory import InMemoryStore


def test_actual_reducer_conservation_and_negative_traces():
    c, ecology = scenario("negative")
    r = CapacityRuntime(InMemoryStore(ecology), c)
    p = r.plan()
    r.event("apply", p, "apply")
    aid = next(a for a, t in p["schedule"].items() if t == 0)
    r.event("dispatch", {"action_id": aid, "reason": "synthetic"}, "dispatch")
    receipt = synthetic_result(c, r.inspect(), aid, "negative")
    receipt["costs"] = [0, 1]
    r.event("tick", {"slot": 1}, "tick")
    r.event("result", receipt, "result")
    r.event("result", receipt, "retry")
    rows = trace(c, r.store.load().archive["capacity_v1"]["events"])
    assert rows[-1]["before"] == rows[-1]["after"]
    for field, delta in (("unfinished", -1), ("reserved", 1), ("authority", 1)):
        bad = deepcopy(rows[-1])
        bad["after"][field] += delta
        with pytest.raises(ValueError):
            evaluate(bad)
    bad = deepcopy(rows[0])
    bad["after"]["completed"] += 1
    bad["after"]["unfinished"] -= 1
    with pytest.raises(ValueError, match="planning"):
        evaluate(bad)
