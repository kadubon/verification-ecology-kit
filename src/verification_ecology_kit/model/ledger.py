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
        residual.status = LedgerStatus.ACTIVE
        self.residuals[residual.residual_id] = residual
        return self._append_event(
            kind="add",
            source_residuals=(),
            target_residuals=(residual.residual_id,),
            justification=justification,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
            provenance=provenance,
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
        return self._append_event(
            kind="merge",
            source_residuals=source_ids,
            target_residuals=(target.residual_id,),
            justification=justification,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
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
        residual = self.residuals[residual_id]
        residual.status = LedgerStatus.RETIRED
        residual.update_links += (reinspection_condition,)
        return self._append_event(
            kind="retire",
            source_residuals=(residual_id,),
            target_residuals=(residual_id,),
            justification=justification,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
        )

    def quarantine(
        self,
        residual_id: str,
        *,
        reason: str,
        actor_authority_ref: str = "local",
    ) -> LedgerEvent:
        pre = self.state_digest()
        residual = self.residuals[residual_id]
        residual.status = LedgerStatus.QUARANTINED
        residual.update_links += (f"recovery_condition:{reason}",)
        return self._append_event(
            kind="quarantine",
            source_residuals=(residual_id,),
            target_residuals=(residual_id,),
            justification=reason,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
        )

    def redact(
        self,
        residual_id: str,
        *,
        reason: str,
        actor_authority_ref: str = "local",
    ) -> tuple[ResidualRecord, LedgerEvent]:
        pre = self.state_digest()
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
        event = self._append_event(
            kind="redact",
            source_residuals=(residual_id,),
            target_residuals=(residual_id, redaction.residual_id),
            justification=reason,
            pre_state_digest=pre,
            actor_authority_ref=actor_authority_ref,
        )
        return redaction, event

    def trace_ok(self) -> CheckResult:
        previous_digest = ""
        for index, event in enumerate(self.events):
            if event.post_state_digest == event.pre_state_digest:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if index > 0 and event.predecessor_event_id != self.events[index - 1].event_id:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            missing_sources = [
                residual_id
                for residual_id in event.source_residuals
                if residual_id not in self.residuals
            ]
            missing_targets = [
                residual_id
                for residual_id in event.target_residuals
                if residual_id not in self.residuals
            ]
            if missing_sources or missing_targets:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            if index == 0:
                if event.pre_state_digest and event.predecessor_event_id is not None:
                    return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
                previous_digest = event.post_state_digest
                continue
            if event.pre_state_digest != previous_digest:
                return fail_result("TraceOK", FailureCode.CANONICALIZATION_DRIFT)
            previous_digest = event.post_state_digest
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
        )
        self.events.append(event)
        return event
