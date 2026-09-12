"""Finite deterministic scenarios and an allowlisted synthetic in-process worker."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from verification_ecology_kit.capacity.model import (
    Action,
    Contract,
    Resource,
    Scenario,
    Service,
    Work,
    digest,
    require,
)
from verification_ecology_kit.capacity.reducer import synthetic_result
from verification_ecology_kit.capacity.runtime import CapacityRuntime
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.records import ResidualKind
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.runtime.engine import RuntimeEngine
from verification_ecology_kit.runtime.in_memory import InMemoryStore

NAMES = (
    "flood",
    "investment",
    "negative",
    "correlated",
    "shared-pool",
    "burst-outage",
    "protected",
    "overpriced",
    "candidate",
    "retry",
    "expiry",
    "integrated",
    "repair",
    "revalidation",
)


def scenario(name: str) -> tuple[Contract, VerifierEcologyState]:
    require(name in NAMES, "unknown capacity example")
    state = VerifierEcologyState()
    horizon = 5 if name in {"investment", "overpriced", "candidate"} else 3
    count = 5 if horizon == 5 else 3
    work = []
    for i in range(count):
        residual = ResidualRecord(
            residual_id=f"res-{i}",
            kind=ResidualKind.UNEXCLUDED,
            origin="synthetic",
            scope=("synthetic-capacity",),
            obligation=f"Required finite synthetic check {i}",
        )
        state.residual_ledger.add(residual, justification="synthetic registered demand")
        work.append(
            Work(
                f"work-{i}",
                residual.residual_id,
                digest(residual.to_dict()),
                digest({"synthetic-case": i}),
                "fixture-rule-v1",
                "finite-check",
                "finite-domain",
                f"bundle-{i}",
                0,
                horizon,
                i == count - 1,
                True,
                (),
                (),
            )
        )
    services: tuple[Service, ...] = (
        Service(
            "base",
            "1",
            "finite-domain",
            ("finite-check",),
            "inert-json-v1",
            horizon,
            ("provider:a", "data:a", "infra:a", "derivation:a"),
            True,
            ("synthetic-fixture-v1",),
            ("finite cases only; no future service guarantee",),
            "synthetic",
        ),
        Service(
            "counter",
            "1",
            "finite-domain",
            ("finite-check",),
            "inert-json-v1",
            horizon,
            ("provider:b", "data:b", "infra:b", "derivation:b"),
            True,
            ("synthetic-counter-v1",),
            ("declared exposure separation only",),
            "synthetic",
        ),
    )
    actions = [
        Action(f"action-{i}", w.work_id, "base", "check", 1, (1, 1), ()) for i, w in enumerate(work)
    ]
    resources = (
        Resource("shared-reviewer", "reviewer-slot", "pool", (1,) * horizon),
        Resource("budget", "cost-unit", "budget", (horizon,)),
    )
    outcomes = ["positive"] * count
    if horizon == 5:
        # Four paid development steps precede the model-only fast service option.
        for i in range(4):
            work[i] = replace(work[i], required=False, protected=False)
            actions[i] = replace(
                actions[i],
                kind=("construct", "calibrate", "counter-check", "activate")[i],
                service_id="counter" if i == 2 else "base",
                requires_success=(f"action-{i - 1}",) if i else (),
            )
        work[2] = replace(work[2], separate_from=("work-1",))
        actions[4] = replace(actions[4], requires_success=("action-3",))
        actions.append(
            Action(
                "fallback", "work-4", "base", "check", 5, (1, 6 if name != "overpriced" else 1), ()
            )
        )
        outcomes.append("positive")
        if name == "candidate":
            outcomes[2] = "invalid"
    if name == "negative":
        outcomes[2] = "negative"
    if name == "repair":
        outcomes[0] = "negative"
        actions[1] = replace(actions[1], kind="repair", requires_negative=("action-0",))
    if name == "revalidation":
        services = (*services, replace(services[0], service_id="renewed", version="2"))
        services = (replace(services[0], valid_until=0), *services[1:])
        actions[0] = replace(actions[0], kind="calibrate", service_id="counter")
        work[0] = replace(work[0], required=False)
        actions[1:] = [
            replace(a, service_id="renewed", requires_success=("action-0",)) for a in actions[1:]
        ]
    if name in {"correlated", "shared-pool"}:
        work[1] = replace(work[1], bundle=work[0].bundle, separate_from=("work-0",))
        actions[1] = replace(actions[1], service_id="counter")
        if name == "correlated":
            services = (services[0], replace(services[1], exposures=services[0].exposures))
    if name == "flood":
        resources = (replace(resources[0], capacity=(1, 0, 0)), resources[1])
    if name == "burst-outage":
        work = [replace(w, arrival=1, deadline=2) for w in work]
        resources = (replace(resources[0], capacity=(3, 0, 3)), resources[1])
    if name == "protected":
        work[2] = replace(work[2], deadline=1)
    if name == "expiry":
        services = (replace(services[0], valid_until=1), services[1])
        work = [replace(w, arrival=1) for w in work]
    c = Contract(
        f"example-{name}",
        "synthetic-capacity",
        "2026-01-01T00:00:00Z",
        "1/2",
        horizon,
        100000,
        256,
        resources,
        services,
        tuple(work),
        tuple(actions),
        (Scenario("declared-joint", tuple(outcomes), "synthetic finite outcome vector"),),
    )
    return c, state


def run_example(name: str) -> dict[str, Any]:
    from verification_ecology_kit.capacity.interchange import cait_envelope, ccr_proposals
    from verification_ecology_kit.capacity.report import capacity_report

    c, state = scenario(name)
    runtime: CapacityRuntime = RuntimeEngine(InMemoryStore(state)).capacity(c)
    allocation = runtime.plan()
    runtime.event("apply", allocation, "apply-0")
    actions = {a.action_id: a for a in c.actions}
    observed = c.scenarios[0].outcomes
    for slot in range(c.horizon + 1):
        runtime.event("tick", {"slot": slot}, f"tick-{slot}")
        for aid in sorted(runtime.inspect().dispatched):
            s = runtime.inspect()
            if s.reservations[aid] + actions[aid].duration == slot:
                result = synthetic_result(
                    c,
                    s,
                    aid,
                    observed[next(i for i, a in enumerate(c.actions) if a.action_id == aid)],
                )
                runtime.event("result", result, f"result-{aid}")
                if name == "retry":
                    runtime.event("result", result, f"retry-{aid}")
        for aid, start in sorted(runtime.inspect().reservations.items()):
            if start != slot:
                continue
            s = runtime.inspect()
            if all(
                s.completed_actions.get(x) == "positive" for x in actions[aid].requires_success
            ) and all(
                s.completed_actions.get(x) == "negative" for x in actions[aid].requires_negative
            ):
                runtime.event(
                    "dispatch",
                    {"action_id": aid, "reason": "allowlisted fixture"},
                    f"dispatch-{aid}",
                )
            else:
                runtime.event(
                    "cancel", {"action_id": aid, "reason": "failed prerequisite"}, f"cancel-{aid}"
                )
    revised = runtime.plan()
    report = capacity_report(c, runtime.inspect(), revised)
    return {
        "name": name,
        "contract": c.to_dict(),
        "plan": allocation,
        "snapshot": runtime.inspect().to_dict(),
        "residuals": sorted(runtime.store.load().residual_ledger.residuals),
        "generated_followups": len(runtime.store.load().packet_population),
        "authority_effect": "none",
        "evidence_basis": "synthetic",
        "revised_plan": revised,
        "capacity_report": report,
        "ccr_proposals": ccr_proposals(
            c, revision="synthetic-ccr-1", pool_ids=[r.resource_id for r in c.resources]
        )
        if name == "integrated"
        else [],
        "cait_envelope": cait_envelope(report) if name == "integrated" else None,
    }
