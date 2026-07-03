"""Append-only residual ledger with traceable operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.digest import DigestPolicy
from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.records import LedgerStatus, ResidualKind, jsonable
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.result import CheckResult, FailureCode, fail_result, pass_result


@dataclass(frozen=True)
class LedgerEvent:
    kind: str
    source_residuals: tuple[str, ...]
    target_residuals: tuple[str, ...]
    justification: str
    pre_state_digest: str
    post_state_digest: str
    actor_authority_ref: str
    policy_id: str
    event_id: str = field(default_factory=lambda: new_id("le"))
    clock_model: str = "total_order"
    conflict_policy: str = "preserve_or_residualize"
    predecessor_event_id: str | None = None
    provenance: tuple[str, ...] = ()
    event_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class TraceCertificate:
    trace_certificate_id: str
    trace_semantics: str
    happens_before_relation_ref: str = ""
    dependency_graph_ref: str = ""
    representative_linearization_refs: tuple[str, ...] = ()
    commutation_evidence_refs: tuple[str, ...] = ()
    conflict_residual_refs: tuple[str, ...] = ()
    visible_ledger_equivalence_target: str = ""
    trace_contract_ref: str = ""
    checker_id: str = ""
    residual_obligations: tuple[str, ...] = ()

    def is_accepted_witness(self) -> bool:
        if self.trace_semantics == "total":
            return True
        return self.trace_semantics == "partial" and bool(
            self.representative_linearization_refs or self.commutation_evidence_refs
        )

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass
class ResidualLedger:
    residuals: dict[str, ResidualRecord] = field(default_factory=dict)
    events: list[LedgerEvent] = field(default_factory=list)
    policy_id: str = "vet-ledger-policy-v1"

    def state_digest(self) -> str:
        state = {
            "residuals": [self.residuals[key].to_dict() for key in sorted(self.residuals)],
            "policy_id": self.policy_id,
        }
        return DigestPolicy().digest_json(state).value

    def add(
        self,
        residual: ResidualRecord,
        *,
        actor_authority_ref: str = "local",
        justification: str = "add residual",
        provenance: tuple[str, ...] = (),
    ) -> LedgerEvent:
        pre = self.state_digest()
        pre_snapshot = self._snapshot()
        residual.status = LedgerStatus.ACTIVE
        self.residuals[residual.residual_id] = residual
        post_snapshot = self._snapshot()
        return self._append_event(
            kind="add",
            source_residuals=(),
            target_residuals=(residual.residual_id,),
            justification=justification,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
            provenance=provenance,
            event_payload=self._delta_payload(
                pre_snapshot,
                post_snapshot,
                dispositions={residual.residual_id: "active"},
                preservation_reasons={
                    residual.residual_id: "ledger_add_preserves_unrouted_residual"
                }
                if residual.route is None
                else {},
            ),
        )

    def merge(
        self,
        source_ids: tuple[str, ...],
        target: ResidualRecord,
        *,
        actor_authority_ref: str = "local",
        justification: str = "merge residuals",
    ) -> LedgerEvent:
        pre = self.state_digest()
        pre_snapshot = self._snapshot()
        missing = [residual_id for residual_id in source_ids if residual_id not in self.residuals]
        if missing:
            target.kind = ResidualKind.CONFLICT_RESIDUAL
            target.obligation = f"Merge referenced missing residuals: {', '.join(missing)}"
        for residual_id in source_ids:
            if residual_id in self.residuals:
                self.residuals[residual_id].status = LedgerStatus.MERGED
                self.residuals[residual_id].update_links += (target.residual_id,)
        target.status = LedgerStatus.ACTIVE
        target.update_links += source_ids
        self.residuals[target.residual_id] = target
        post_snapshot = self._snapshot()
        return self._append_event(
            kind="merge",
            source_residuals=source_ids,
            target_residuals=(target.residual_id,),
            justification=justification,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
            event_payload=self._delta_payload(
                pre_snapshot,
                post_snapshot,
                missing_sources=missing,
                dispositions={
                    **{
                        residual_id: "merged"
                        for residual_id in source_ids
                        if residual_id in pre_snapshot
                    },
                    target.residual_id: "active",
                },
                preservation_reasons={
                    target.residual_id: "merge_preserves_or_conflict-residualizes_sources"
                }
                if target.route is None
                else {},
            ),
        )

    def retire(
        self,
        residual_id: str,
        *,
        justification: str,
        actor_authority_ref: str = "local",
        reinspection_condition: str = "manual_reinspection",
    ) -> LedgerEvent:
        pre = self.state_digest()
        pre_snapshot = self._snapshot()
        residual = self.residuals[residual_id]
        residual.status = LedgerStatus.RETIRED
        residual.update_links += (reinspection_condition,)
        post_snapshot = self._snapshot()
        return self._append_event(
            kind="retire",
            source_residuals=(residual_id,),
            target_residuals=(residual_id,),
            justification=justification,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
            event_payload=self._delta_payload(
                pre_snapshot,
                post_snapshot,
                reinspection_condition=reinspection_condition,
                dispositions={residual_id: "retired"},
            ),
        )

    def quarantine(
        self,
        residual_id: str,
        *,
        reason: str,
        actor_authority_ref: str = "local",
    ) -> LedgerEvent:
        pre = self.state_digest()
        pre_snapshot = self._snapshot()
        residual = self.residuals[residual_id]
        residual.status = LedgerStatus.QUARANTINED
        residual.update_links += (f"recovery_condition:{reason}",)
        post_snapshot = self._snapshot()
        return self._append_event(
            kind="quarantine",
            source_residuals=(residual_id,),
            target_residuals=(residual_id,),
            justification=reason,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
            event_payload=self._delta_payload(
                pre_snapshot,
                post_snapshot,
                recovery_condition=reason,
                dispositions={residual_id: "quarantined"},
            ),
        )

    def redact(
        self,
        residual_id: str,
        *,
        reason: str,
        actor_authority_ref: str = "local",
    ) -> tuple[ResidualRecord, LedgerEvent]:
        pre = self.state_digest()
        pre_snapshot = self._snapshot()
        residual = self.residuals[residual_id]
        residual.status = LedgerStatus.REDACTED
        residual.payload = {}
        redaction = ResidualRecord(
            kind=ResidualKind.REDACTION_RESIDUAL,
            origin=residual_id,
            scope=residual.scope,
            obligation="Preserve authority loss and provenance after redaction",
            exposure=residual.exposure,
            update_links=(residual_id,),
            provenance=residual.provenance,
        )
        self.residuals[redaction.residual_id] = redaction
        post_snapshot = self._snapshot()
        event = self._append_event(
            kind="redact",
            source_residuals=(residual_id,),
            target_residuals=(residual_id, redaction.residual_id),
            justification=reason,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
            event_payload=self._delta_payload(
                pre_snapshot,
                post_snapshot,
                redaction_consequence=redaction.residual_id,
                dispositions={
                    residual_id: "redacted",
                    redaction.residual_id: "redaction_residual_active",
                },
                preservation_reasons={
                    redaction.residual_id: "redaction_residual_preserves_authority_loss"
                },
            ),
        )
        return redaction, event

    def trace_ok(self) -> CheckResult:
        replay_state: dict[str, dict[str, Any]] = {}
        previous_event_id: str | None = None
        for event in self.events:
            if event.clock_model != "total_order" and not self._trace_certificate_ok(event):
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if event.kind != "add" and not event.source_residuals:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if not event.target_residuals:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            expected_pre = self._state_digest_for(replay_state)
            if event.pre_state_digest != expected_pre:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if event.predecessor_event_id != previous_event_id:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            post_residuals = event.event_payload.get("post_residuals")
            if not isinstance(post_residuals, dict):
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            for residual_id in event.source_residuals:
                if residual_id not in replay_state:
                    target = self._event_target_snapshot(event, post_residuals)
                    if (
                        event.kind != "merge"
                        or target.get("kind") != ResidualKind.CONFLICT_RESIDUAL.value
                    ):
                        return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            for residual_id in event.target_residuals:
                if residual_id not in post_residuals:
                    return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if event.kind == "redact" and not any(
                post_residuals[target].get("kind") == ResidualKind.REDACTION_RESIDUAL.value
                for target in event.target_residuals
                if target in post_residuals
            ):
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if event.kind == "retire" and (
                not event.justification.strip()
                or not event.event_payload.get("reinspection_condition")
            ):
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            expected_post = self._state_digest_for(post_residuals)
            if event.post_state_digest != expected_post:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            replay_state = {
                str(key): value for key, value in post_residuals.items() if isinstance(value, dict)
            }
            previous_event_id = event.event_id
        if self._state_digest_for(self._snapshot()) != self._state_digest_for(replay_state):
            return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
        for residual_id, residual in replay_state.items():
            if residual.get("status") != LedgerStatus.ACTIVE.value:
                continue
            route = residual.get("route")
            if route is not None:
                continue
            if not self._active_unrouted_preserved(residual_id):
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
        return pass_result("TraceOK")

    def to_dict(self) -> dict[str, Any]:
        return {
            "residuals": [self.residuals[key].to_dict() for key in sorted(self.residuals)],
            "events": [event.to_dict() for event in self.events],
            "policy_id": self.policy_id,
        }

    def _append_event(
        self,
        *,
        kind: str,
        source_residuals: tuple[str, ...],
        target_residuals: tuple[str, ...],
        justification: str,
        pre_state_digest: str,
        actor_authority_ref: str,
        provenance: tuple[str, ...] = (),
        event_payload: dict[str, Any] | None = None,
    ) -> LedgerEvent:
        predecessor = self.events[-1].event_id if self.events else None
        post = self.state_digest()
        event = LedgerEvent(
            kind=kind,
            source_residuals=source_residuals,
            target_residuals=target_residuals,
            justification=justification,
            pre_state_digest=pre_state_digest,
            post_state_digest=post,
            actor_authority_ref=actor_authority_ref,
            policy_id=self.policy_id,
            predecessor_event_id=predecessor,
            provenance=provenance,
            event_payload=event_payload or {},
        )
        self.events.append(event)
        return event

    def _snapshot(self) -> dict[str, dict[str, Any]]:
        return {key: self.residuals[key].to_dict() for key in sorted(self.residuals)}

    def _delta_payload(
        self,
        pre_snapshot: dict[str, dict[str, Any]],
        post_snapshot: dict[str, dict[str, Any]],
        **extra: Any,
    ) -> dict[str, Any]:
        changed = {
            residual_id: post_snapshot[residual_id]
            for residual_id in post_snapshot
            if pre_snapshot.get(residual_id) != post_snapshot[residual_id]
        }
        removed = sorted(set(pre_snapshot) - set(post_snapshot))
        payload = {
            "pre_residuals": pre_snapshot,
            "post_residuals": post_snapshot,
            "delta": {"changed": changed, "removed": removed},
        }
        payload.update(extra)
        return payload

    def _state_digest_for(self, residuals: dict[str, dict[str, Any]]) -> str:
        state = {
            "residuals": [residuals[key] for key in sorted(residuals)],
            "policy_id": self.policy_id,
        }
        return DigestPolicy().digest_json(state).value

    def _event_target_snapshot(
        self, event: LedgerEvent, post_residuals: dict[str, Any]
    ) -> dict[str, Any]:
        if not event.target_residuals:
            return {}
        target = post_residuals.get(event.target_residuals[0])
        return target if isinstance(target, dict) else {}

    def _trace_certificate_ok(self, event: LedgerEvent) -> bool:
        raw = event.event_payload.get("trace_certificate")
        if isinstance(raw, TraceCertificate):
            return raw.is_accepted_witness()
        if not isinstance(raw, dict):
            return False
        certificate = TraceCertificate(
            trace_certificate_id=str(raw.get("trace_certificate_id", "")),
            trace_semantics=str(raw.get("trace_semantics", "")),
            happens_before_relation_ref=str(raw.get("happens_before_relation_ref", "")),
            dependency_graph_ref=str(raw.get("dependency_graph_ref", "")),
            representative_linearization_refs=tuple(
                str(item) for item in raw.get("representative_linearization_refs", ())
            ),
            commutation_evidence_refs=tuple(
                str(item) for item in raw.get("commutation_evidence_refs", ())
            ),
            conflict_residual_refs=tuple(
                str(item) for item in raw.get("conflict_residual_refs", ())
            ),
            visible_ledger_equivalence_target=str(raw.get("visible_ledger_equivalence_target", "")),
            trace_contract_ref=str(raw.get("trace_contract_ref", "")),
            checker_id=str(raw.get("checker_id", "")),
            residual_obligations=tuple(str(item) for item in raw.get("residual_obligations", ())),
        )
        return certificate.is_accepted_witness()

    def _active_unrouted_preserved(self, residual_id: str) -> bool:
        for event in reversed(self.events):
            raw = event.event_payload.get("preservation_reasons")
            if isinstance(raw, dict) and str(raw.get(residual_id, "")).strip():
                return True
        return False
