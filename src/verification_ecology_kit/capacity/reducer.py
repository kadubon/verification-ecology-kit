"""Explicit single-writer event replay; reservations never execute external work."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from verification_ecology_kit.capacity.checker import Snapshot, check_plan
from verification_ecology_kit.capacity.model import (
    Contract,
    digest,
    natural,
    require,
    validate_schema,
)


def replay(c: Contract, events: list[dict[str, Any]]) -> Snapshot:
    require(len(events) <= c.max_events, "history bound exceeded")
    state = Snapshot(spent=[0] * len(c.resources))
    seen: dict[str, str] = {}
    for event in events:
        require(set(event) == {"event_id", "revision", "kind", "payload"}, "invalid event fields")
        eid = event["event_id"]
        require(isinstance(eid, str) and 0 < len(eid) <= 128, "invalid event identity")
        fingerprint = digest(event)
        natural(event["revision"], c.max_events)
        if eid in seen:
            require(seen[eid] == fingerprint, "conflicting duplicate event")
            continue
        require(event["revision"] == state.revision, "stale event revision")
        state = reduce_event(c, state, event["kind"], event["payload"])
        state.revision += 1
        seen[eid] = fingerprint
    return state


def reduce_event(c: Contract, previous: Snapshot, kind: str, p: dict[str, Any]) -> Snapshot:
    s = deepcopy(previous)
    actions = {a.action_id: a for a in c.actions}
    works = {w.work_id: w for w in c.work}
    services = {v.service_id: v for v in c.services}
    if kind == "apply":
        check_plan(c, s, p)
        s.reservations.update(p["schedule"])
    elif kind == "tick":
        require(set(p) == {"slot"}, "invalid clock fields")
        natural(p["slot"], c.horizon)
        require(p["slot"] >= s.clock, "clock reversal")
        s.clock = p["slot"]
    elif kind == "withdraw":
        require(
            set(p) == {"service_id", "reason"} and bool(p["reason"]), "withdrawal reason required"
        )
        require(p["service_id"] in services, "unknown service")
        s.withdrawn.add(p["service_id"])
    elif kind in {"dispatch", "cancel"}:
        require(set(p) == {"action_id", "reason"} and bool(p["reason"]), "action/reason required")
        aid = p["action_id"]
        require(aid in s.reservations, "unreserved action")
        a = actions[aid]
        if kind == "cancel":
            require(
                aid not in s.dispatched and s.clock <= s.reservations[aid],
                "unknown/started work cannot be cancelled",
            )
            del s.reservations[aid]
            # Cancellation removes this unstarted attempt, never its source obligation.
        else:
            require(
                aid not in s.dispatched and s.clock == s.reservations[aid],
                "duplicate or late dispatch",
            )
            require(a.service_id not in s.withdrawn, "withdrawn service")
            require(s.clock + a.duration <= services[a.service_id].valid_until, "expired service")
            require(
                all(x in s.completed for x in works[a.work_id].predecessors),
                "predecessor unfinished",
            )
            require(
                all(s.completed_actions.get(x) == "positive" for x in a.requires_success),
                "activation not admitted",
            )
            require(
                all(s.completed_actions.get(x) == "negative" for x in a.requires_negative),
                "negative-check prerequisite not admitted",
            )
            s.dispatched.add(aid)
            s.attempts[aid] = s.attempts.get(aid, 0) + 1
    elif kind == "result":
        _result(c, s, p)
    elif kind == "followup":
        require(
            set(p)
            == {
                "work_id",
                "subject_digest",
                "source_residual",
                "rule_version",
                "arrival",
                "parent_work",
            },
            "invalid follow-up fields",
        )
        require(p["parent_work"] in s.completed, "follow-up parent not completed")
        require(
            p["source_residual"] == works[p["parent_work"]].residual_id,
            "follow-up source substitution",
        )
        require(p["arrival"] == s.clock, "follow-up arrival mismatch")
        key = p["work_id"]
        require(key not in s.followups or s.followups[key] == p, "conflicting follow-up identity")
        require(key in s.followups or len(s.followups) < len(c.work), "follow-up bound exceeded")
        s.followups[key] = deepcopy(p)
    else:
        raise ValueError("unsupported event kind")
    return s


def _result(c: Contract, s: Snapshot, p: dict[str, Any]) -> None:
    validate_schema("capacity-result", p)
    fields = {
        "result_id",
        "action_id",
        "work_id",
        "subject_digest",
        "input_digest",
        "service_id",
        "service_version",
        "interface",
        "attempt",
        "outcome",
        "costs",
        "start",
        "end",
        "completed_work",
        "evidence_basis",
        "support_refs",
        "contract_digest",
        "scope",
    }
    require(set(p) == fields, "invalid result fields")
    rid = p["result_id"]
    fingerprint = digest(p)
    if rid in s.results:
        require(s.results[rid] == fingerprint, "conflicting duplicate result")
        return
    actions = {a.action_id: a for a in c.actions}
    aid = p["action_id"]
    require(aid in s.dispatched and aid in s.reservations, "result has no dispatched reservation")
    a = actions[aid]
    w = next(w for w in c.work if w.work_id == a.work_id)
    v = next(v for v in c.services if v.service_id == a.service_id)
    for key, expected in {
        "work_id": w.work_id,
        "subject_digest": w.subject_digest,
        "input_digest": w.input_digest,
        "service_id": v.service_id,
        "service_version": v.version,
        "interface": v.interface,
        "attempt": s.attempts[aid],
        "start": s.reservations[aid],
        "end": s.reservations[aid] + a.duration,
        "scope": c.scope,
        "contract_digest": c.contract_digest,
        "support_refs": list(v.support_refs),
    }.items():
        require(p[key] == expected, f"result binding mismatch: {key}")
    require(
        p["end"] <= s.clock and v.service_id not in s.withdrawn and p["end"] <= v.valid_until,
        "premature or withdrawn result",
    )
    # This local profile admits synthetic/declared accounting only. Caller labels can
    # never mint authenticated operational service observations or VET authority.
    require(
        p["evidence_basis"] == v.evidence_basis
        and p["evidence_basis"] in {"synthetic", "declared-model"},
        "observed service requires an authenticated host adapter; unsupported locally",
    )
    require(
        p["outcome"] in {"positive", "negative", "invalid", "inconclusive", "timeout"},
        "unknown outcome",
    )
    natural(p["completed_work"], 1)
    require(
        p["completed_work"] == int(p["outcome"] in {"positive", "negative"}),
        "unqualified work completion",
    )
    require(len(p["costs"]) == len(c.resources), "cost coordinates mismatch")
    for i, r in enumerate(c.resources):
        natural(p["costs"][i])
        maximum = a.costs[i] * (a.duration if r.kind == "pool" else 1)
        require(p["costs"][i] <= maximum, "result exceeds reservation")
        s.spent[i] += p["costs"][i]
    if p["completed_work"]:
        s.completed[w.work_id] = p["outcome"]
        s.completion_times[w.work_id] = p["end"]
        if p["outcome"] == "negative":
            s.repair.add(w.work_id)
        if a.kind == "repair" and p["outcome"] == "positive":
            s.repair -= {actions[x].work_id for x in a.requires_negative}
    s.completed_actions[aid] = p["outcome"]
    s.results[rid] = fingerprint
    del s.reservations[aid]
    s.dispatched.remove(aid)


def synthetic_result(c: Contract, s: Snapshot, aid: str, outcome: str) -> dict[str, Any]:
    """Inert deterministic fixture receipt; cannot be relabeled as observed evidence."""
    a = next(a for a in c.actions if a.action_id == aid)
    w = next(w for w in c.work if w.work_id == a.work_id)
    v = next(v for v in c.services if v.service_id == a.service_id)
    return {
        "result_id": f"{aid}:{s.attempts[aid]}",
        "action_id": aid,
        "work_id": w.work_id,
        "subject_digest": w.subject_digest,
        "input_digest": w.input_digest,
        "service_id": v.service_id,
        "service_version": v.version,
        "interface": v.interface,
        "attempt": s.attempts[aid],
        "outcome": outcome,
        "start": s.reservations[aid],
        "end": s.reservations[aid] + a.duration,
        "costs": [
            a.costs[i] * (a.duration if r.kind == "pool" else 1) for i, r in enumerate(c.resources)
        ],
        "completed_work": int(outcome in {"positive", "negative"}),
        "evidence_basis": "synthetic",
        "support_refs": list(v.support_refs),
        "contract_digest": c.contract_digest,
        "scope": c.scope,
    }
