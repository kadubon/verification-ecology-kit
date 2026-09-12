"""Adverse controls for the finite model, independent checker and explicit reducer."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest
from jsonschema import ValidationError

from verification_ecology_kit.capacity.checker import Snapshot, check_plan, check_schedule
from verification_ecology_kit.capacity.examples import NAMES, run_example, scenario
from verification_ecology_kit.capacity.interchange import cait_envelope, ccr_proposals
from verification_ecology_kit.capacity.model import Contract
from verification_ecology_kit.capacity.reducer import reduce_event, replay, synthetic_result
from verification_ecology_kit.capacity.report import capacity_report
from verification_ecology_kit.capacity.runtime import CapacityRuntime
from verification_ecology_kit.capacity.selector import plan
from verification_ecology_kit.model.records import Visibility
from verification_ecology_kit.runtime.engine import RuntimeEngine
from verification_ecology_kit.runtime.in_memory import InMemoryStore
from verification_ecology_kit.runtime.loop import DefaultPacketGenerator


def setup(name="negative"):
    c, ecology = scenario(name)
    return c, CapacityRuntime(InMemoryStore(ecology), c)


@pytest.mark.parametrize("name", NAMES)
def test_installed_native_scenarios(name):
    result = run_example(name)
    assert result["authority_effect"] == "none"
    assert result["plan"]["search"]["complete"]
    assert len(result["residuals"]) >= len(result["contract"]["work"])
    if name == "negative":
        assert result["snapshot"]["completed"]["work-2"] == "negative"
        assert result["snapshot"]["repair"] == ["work-2"]
        assert len(result["residuals"]) == 4
        assert len(result["snapshot"]["followups"]) == 3
        assert result["capacity_report"]["local_accounting"]["unfinished"] == 3
    if name == "investment":
        assert "work-4" in result["snapshot"]["completed"]
        assert "action-3" in result["plan"]["schedule"]
    if name == "overpriced":
        assert result["plan"]["schedule"] == {"fallback": 0}
    if name in {"burst-outage", "expiry", "candidate"}:
        assert result["plan"]["search"]["status"] == "infeasible"
    if name == "protected":
        assert result["plan"]["schedule"]["action-2"] == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("horizon", True),
        ("horizon", -1),
        ("horizon", 1.5),
        ("horizon", 1.0),
        ("horizon", 1000),
        ("slot_seconds", "0"),
        ("slot_seconds", "1/0"),
        ("slot_seconds", "1e3"),
        ("semantics", "preemptive"),
        ("schema_version", "v2"),
        ("scenarios", []),
        ("work_unit", "tokens"),
        ("max_events", 0),
        ("max_candidates", 1_000_001),
    ],
)
def test_malformed_contracts(field, value):
    c, _ = scenario("flood")
    data = c.to_dict()
    data[field] = value
    with pytest.raises((ValueError, ValidationError)):
        Contract.from_dict(data)


def test_closed_records_and_semantic_validation():
    c, _ = scenario("flood")
    assert Contract.from_dict(c.to_dict()) == c
    changes = [
        replace(c.work[0], predecessors=("missing",)),
        replace(c.work[0], predecessors=("work-0",)),
        replace(c.work[0], arrival=2, deadline=1),
    ]
    for w in changes:
        with pytest.raises(ValueError):
            replace(c, work=(w, *c.work[1:]))
    with pytest.raises(ValueError, match="duplicate"):
        replace(c, work=(c.work[0], c.work[0], c.work[2]))
    with pytest.raises(ValueError, match="cyclic"):
        replace(
            c,
            actions=(
                replace(c.actions[0], requires_success=("action-1",)),
                replace(c.actions[1], requires_success=("action-0",)),
                c.actions[2],
            ),
        )
    for action in [
        replace(c.actions[0], costs=(1,)),
        replace(c.actions[0], service_id="missing"),
        replace(c.actions[0], requires_success=("missing",)),
        replace(c.actions[0], duration=4),
    ]:
        with pytest.raises(ValueError):
            replace(c, actions=(action, *c.actions[1:]))
    with pytest.raises(ValueError):
        replace(c, scenarios=(replace(c.scenarios[0], outcomes=("positive",)),))
    with pytest.raises(ValueError):
        replace(c, resources=(replace(c.resources[0], capacity=(1,)), c.resources[1]))
    data = c.to_dict()
    data["objective_weights"] = {"acceptance": 100}
    with pytest.raises(ValidationError):
        Contract.from_dict(data)


def test_schedule_resources_separation_and_expiry():
    c, runtime = setup("shared-pool")
    s = runtime.inspect()
    with pytest.raises(ValueError, match="shared pool"):
        check_schedule(c, s, {"action-0": 0, "action-1": 0})
    check_schedule(c, s, {"action-0": 0, "action-1": 1})
    correlated, r = setup("correlated")
    with pytest.raises(ValueError, match="separation"):
        check_schedule(correlated, r.inspect(), {"action-0": 0, "action-1": 1})
    unknown = replace(c, services=(replace(c.services[0], dependence_known=False), c.services[1]))
    with pytest.raises(ValueError, match="separation"):
        check_schedule(unknown, s, {"action-0": 0, "action-1": 1})
    expired, r = setup("expiry")
    with pytest.raises(ValueError, match="expired"):
        check_schedule(expired, r.inspect(), {"action-0": 1})
    for schedule in ({"missing": 0}, {"action-0": -1}, {"action-0": 3}, {"action-0": 0.5}):
        with pytest.raises(ValueError):
            check_schedule(c, s, schedule)
    s.withdrawn.add("base")
    with pytest.raises(ValueError, match="withdrawn"):
        check_schedule(c, s, {"action-0": 0})


def test_plan_read_only_stale_and_witness_tampering():
    c, r = setup()
    original = deepcopy(r.store.load().to_dict())
    p = r.plan()
    assert r.store.load().to_dict() == original
    tampered = deepcopy(p)
    tampered["checked"]["objective"][0] = "100"
    with pytest.raises(ValueError, match="tampered"):
        check_plan(c, r.inspect(), tampered)
    r.event("apply", p, "apply")
    with pytest.raises(ValueError, match="stale"):
        r.event("apply", p, "apply-again")
    with pytest.raises(ValueError, match="already reserved"):
        check_schedule(c, r.inspect(), p["schedule"])
    limited = replace(c, max_candidates=1)
    result = plan(limited, Snapshot(spent=[0, 0]))
    assert result["search"]["status"] == "unknown"
    assert not result["search"]["complete"]


def dispatched():
    c, r = setup()
    p = r.plan()
    r.event("apply", p, "apply")
    aid = next(a for a, t in p["schedule"].items() if t == 0)
    r.event("dispatch", {"action_id": aid, "reason": "fixture"}, "dispatch")
    return c, r, aid


@pytest.mark.parametrize(
    "field,value",
    [
        ("subject_digest", "a" * 64),
        ("input_digest", "b" * 64),
        ("work_id", "substitute"),
        ("service_version", "2"),
        ("service_id", "counter"),
        ("scope", "elsewhere"),
        ("interface", "other"),
        ("attempt", 2),
        ("start", 1),
        ("end", 0),
        ("contract_digest", "c" * 64),
        ("support_refs", []),
        ("evidence_basis", "observed-record"),
        ("outcome", "fake"),
        ("completed_work", 0.5),
        ("costs", [-1, 1]),
        ("costs", [1000, 1]),
        ("costs", [1]),
    ],
)
def test_result_substitution_and_bad_effects(field, value):
    c, r, aid = dispatched()
    result = synthetic_result(c, r.inspect(), aid, "positive")
    r.event("tick", {"slot": 1}, "tick")
    result[field] = value
    before = r.store.load().to_dict()
    with pytest.raises((ValueError, ValidationError)):
        r.event("result", result, "bad")
    assert r.store.load().to_dict() == before


@pytest.mark.parametrize("outcome", ["positive", "negative", "invalid", "timeout", "inconclusive"])
def test_attempt_accounting_retry_and_unknown_dispatch(outcome):
    c, r, aid = dispatched()
    result = synthetic_result(c, r.inspect(), aid, outcome)
    with pytest.raises(ValueError, match="premature"):
        r.event("result", result, "early")
    with pytest.raises(ValueError, match="cannot be cancelled"):
        r.event("cancel", {"action_id": aid, "reason": "unknown dispatch"}, "cancel")
    r.event("tick", {"slot": 1}, "tick")
    r.event("result", result, "result")
    before = r.inspect()
    packets = len(r.store.load().packet_population)
    r.event("result", result, "retry")
    assert r.inspect().spent == before.spent
    assert len(r.store.load().packet_population) == packets
    result["costs"] = [0, 0]
    with pytest.raises(ValueError, match="conflicting duplicate"):
        r.event("result", result, "conflict")
    assert bool(r.inspect().completed) == (outcome in {"positive", "negative"})


def test_replay_duplicate_and_cancel_withdraw():
    c, r = setup()
    event = {"event_id": "apply", "revision": 0, "kind": "apply", "payload": r.plan()}
    r.update(event)
    r.update(event)
    assert r.inspect().revision == 1
    bad = deepcopy(event)
    bad["payload"]["schedule"] = {}
    with pytest.raises(ValueError, match="conflicting duplicate"):
        r.update(bad)
    aid = next(iter(r.inspect().reservations))
    r.event("cancel", {"action_id": aid, "reason": "provably unstarted"}, "cancel")
    assert aid not in r.inspect().reservations
    assert not r.inspect().completed
    r.event("withdraw", {"service_id": "base", "reason": "expired support"}, "withdraw")
    with pytest.raises(ValueError):
        r.event("tick", {"slot": -1}, "bad-tick")
    with pytest.raises(ValueError):
        r.event("unknown", {}, "unknown")
    with pytest.raises(ValueError):
        replay(replace(c, max_events=1), [event, event])
    with pytest.raises(ValueError):
        replay(c, [{"event_id": "bad"}])


def test_runtime_source_binding_contract_change_and_atomic_failure(monkeypatch):
    _c, r = setup()
    p = r.plan()
    r.store.load().residual_ledger.residuals["res-0"].obligation = "changed"
    with pytest.raises(ValueError, match="source residual changed"):
        r.event("apply", p, "apply")
    _c, r = setup()
    original = deepcopy(r.store.load().to_dict())

    def interrupted(_state):
        raise OSError("simulated interrupted store write")

    monkeypatch.setattr(r.store, "save", interrupted)
    with pytest.raises(OSError):
        r.event("apply", r.plan(), "apply")
    assert r.store.load().to_dict() == original


def test_report_and_pinned_companion_contract():
    c, r = setup("integrated")
    report = capacity_report(c, r.inspect(), r.plan())
    assert report["observed_service"] is None
    assert report["service_guaranteed_lower_envelope"] is None
    assert cait_envelope(report)["arrival_verdict"] is None
    assert len(ccr_proposals(c, revision="ccr-revision-1", pool_ids=["pool", "budget"])) == 3
    longer = replace(c, slot_seconds="61")
    assert ccr_proposals(longer, revision="1", pool_ids=["p", "b"])[0]["constraints"][
        "max_runtime_minutes"] == 2
    with pytest.raises(ValueError, match="duration exceeds"):
        ccr_proposals(replace(c, slot_seconds="1000000"), revision="1", pool_ids=["p", "b"])
    with pytest.raises(ValueError):
        ccr_proposals(c, revision="1", pool_ids=[], schema_version="unknown")
    with pytest.raises(ValueError):
        ccr_proposals(c, revision="", pool_ids=[])


def test_hidden_joint_scenario_is_not_an_input_to_selection():
    c, r = setup()
    adverse = replace(c.scenarios[0], scenario_id="outage", outcomes=("timeout",) * 3)
    c = replace(c, scenarios=(*c.scenarios, adverse))
    result = plan(c, r.inspect())
    assert not result["checked"]["mandatory_met"]
    assert result["search"]["status"] == "infeasible"
    assert len(result["checked"]["branches"]) == 2
    assert "scenario_id" not in result["schedule"]


def test_each_robust_objective_coordinate_uses_all_joint_branches():
    c, r = setup()
    c = replace(
        c,
        scenarios=(
            replace(c.scenarios[0], scenario_id="a", outcomes=("positive", "positive", "timeout")),
            replace(c.scenarios[0], scenario_id="b", outcomes=("timeout", "timeout", "positive")),
        ),
    )
    result = plan(c, r.inspect())
    assert result["checked"]["objective"][:2] == ["0", "1/3"]


def test_success_prerequisite_and_completed_work_cannot_be_rescheduled():
    c, r = setup("investment")
    with pytest.raises(ValueError, match="prerequisite"):
        check_schedule(c, r.inspect(), {"action-4": 4})
    s = Snapshot(spent=[0, 0], completed={"work-4": "positive"})
    with pytest.raises(ValueError, match="no longer pending"):
        check_schedule(c, s, {"action-4": 4})
    with pytest.raises(ValueError, match="predecessor"):
        dependent = replace(c, work=(*c.work[:4], replace(c.work[4], predecessors=("work-0",))))
        check_schedule(dependent, r.inspect(), {"action-4": 4})
    s = reduce_event(c, r.inspect(), "tick", {"slot": 1})
    with pytest.raises(ValueError, match="reversal"):
        reduce_event(c, s, "tick", {"slot": 0})


def test_capacity_respects_host_generator_and_quarantine_policy():
    c, ecology = scenario("negative")
    calls = []

    class Generator:
        def from_residual(self, residual):
            calls.append(residual.residual_id)
            return DefaultPacketGenerator().from_residual(residual)

    class Policy:
        def should_quarantine(self, packet):
            return True

    runtime = RuntimeEngine(InMemoryStore(ecology), Generator(), Policy()).capacity(c)
    allocation = runtime.plan()
    runtime.event("apply", allocation, "apply")
    aid = next(a for a, start in allocation["schedule"].items() if start == 0)
    runtime.event("dispatch", {"action_id": aid, "reason": "fixture"}, "dispatch")
    result = synthetic_result(c, runtime.inspect(), aid, "positive")
    runtime.event("tick", {"slot": 1}, "tick")
    runtime.event("result", result, "result")
    assert len(calls) == 1
    packet = next(iter(runtime.store.load().packet_population.values()))
    assert packet.circulation_status.visibility == Visibility.QUARANTINED
    assert runtime.store.load().residual_ledger.residuals[calls[0]].status.value == "active"
