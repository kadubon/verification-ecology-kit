"""Packet operation engine."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.packets import (
    REQUIRED_CORE_FIELDS,
    BoundaryRefs,
    CirculationStatus,
    PacketOrigin,
    VerifierPacket,
)
from verification_ecology_kit.model.records import (
    OriginKind,
    ResidualKind,
    TrustStatus,
    Visibility,
    jsonable,
)
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.result import (
    CheckResult,
    FailureCode,
    fail_result,
    pass_result,
    residual_result,
)


class PacketOperationName(StrEnum):
    FORK = "fork"
    SPECIALIZE = "specialize"
    GENERALIZE = "generalize"
    COMPOSE = "compose"
    CONTRAST = "contrast"
    REPAIR = "repair"
    RETIRE = "retire"
    QUARANTINE = "quarantine"
    INTERNALIZE = "internalize"
    REDACT = "redact"


@dataclass
class OperationReport:
    operation: PacketOperationName
    input_packet_ids: tuple[str, ...]
    output_packet: VerifierPacket | None
    admissibility: CheckResult
    core_monotonicity: CheckResult
    residual_totality: CheckResult
    boundary_safety: CheckResult
    schema_overclosure_risk: CheckResult = field(
        default_factory=lambda: pass_result("SchemaOverclosureRisk")
    )
    lineage_laundering: CheckResult = field(
        default_factory=lambda: pass_result("LineageLaundering")
    )
    ledger_event_refs: tuple[str, ...] = ()
    residual_refs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass
class PacketOperationEngine:
    ledger: ResidualLedger = field(default_factory=ResidualLedger)

    def fork(self, packet: VerifierPacket, *, reason: str = "fork") -> OperationReport:
        child = copy.deepcopy(packet)
        child.packet_id = new_id("pkt")
        if child.origin is None:
            child.origin = PacketOrigin(created_from=OriginKind.RESIDUAL)
        child.origin.lineage.append(packet.packet_id)
        child.origin.parent_packets.append(packet.packet_id)
        child.origin.inherited_residuals.extend(
            residual.residual_id for residual in packet.residual_obligations
        )
        return self._finalize(PacketOperationName.FORK, (packet,), child, reason=reason)

    def specialize(self, packet: VerifierPacket, *, scope: str) -> OperationReport:
        child = copy.deepcopy(packet)
        child.packet_id = new_id("pkt")
        if child.scope is not None:
            child.scope.applies_to.append(scope)
        return self._finalize(PacketOperationName.SPECIALIZE, (packet,), child, reason="specialize")

    def generalize(
        self, packet: VerifierPacket, *, residualize_scope_loss: bool = True
    ) -> OperationReport:
        child = copy.deepcopy(packet)
        child.packet_id = new_id("pkt")
        residuals: list[ResidualRecord] = []
        if residualize_scope_loss:
            residual = ResidualRecord(
                kind=ResidualKind.UNEXCLUDED,
                origin=packet.packet_id,
                scope=("generalization",),
                obligation="Generalized packet requires new boundary and scope checks",
                exposure="blocks_support",
            )
            child.residual_obligations.append(residual)
            residuals.append(residual)
        return self._finalize(
            PacketOperationName.GENERALIZE,
            (packet,),
            child,
            reason="generalize",
            extra_residuals=residuals,
            boundary_checked=not residualize_scope_loss,
        )

    def compose(self, left: VerifierPacket, right: VerifierPacket) -> OperationReport:
        child = copy.deepcopy(left)
        child.packet_id = new_id("pkt")
        if child.origin is None:
            child.origin = PacketOrigin(created_from=OriginKind.CONTRAST)
        child.origin.lineage.extend([left.packet_id, right.packet_id])
        child.origin.parent_packets.extend([left.packet_id, right.packet_id])
        child.origin.inherited_residuals.extend(
            residual.residual_id
            for packet in (left, right)
            for residual in packet.residual_obligations
        )
        existing_residual_ids = {residual.residual_id for residual in child.residual_obligations}
        for residual in right.residual_obligations:
            if residual.residual_id not in existing_residual_ids:
                child.residual_obligations.append(copy.deepcopy(residual))
                existing_residual_ids.add(residual.residual_id)
        if child.boundary_refs is None:
            child.boundary_refs = BoundaryRefs()
        child.boundary_refs.reachability_certificate_refs = []
        residual = ResidualRecord(
            kind=ResidualKind.UNEXCLUDED,
            origin=child.packet_id,
            scope=("composition", "reachability"),
            obligation="Composition requires its own boundary and reachability checks",
            exposure="blocks_support",
        )
        child.residual_obligations.append(residual)
        counter_residual = ResidualRecord(
            kind=ResidualKind.MISSING_COUNTER,
            origin=child.packet_id,
            scope=("composition", "counter_packet"),
            obligation="Composition requires a new counter-packet obligation",
            exposure="blocks_support",
        )
        child.residual_obligations.append(counter_residual)
        return self._finalize(
            PacketOperationName.COMPOSE,
            (left, right),
            child,
            reason="compose",
            extra_residuals=[residual, counter_residual],
            boundary_checked=False,
        )

    def contrast(self, left: VerifierPacket, right: VerifierPacket) -> OperationReport:
        child = VerifierPacket.minimal(created_from=OriginKind.CONTRAST)
        assert child.origin is not None
        child.origin.lineage.extend([left.packet_id, right.packet_id])
        child.question_form = {"contrast": [left.packet_id, right.packet_id]}
        return self._finalize(PacketOperationName.CONTRAST, (left, right), child, reason="contrast")

    def repair(self, packet: VerifierPacket, *, repair_note: str) -> OperationReport:
        child = copy.deepcopy(packet)
        child.packet_id = new_id("pkt")
        if child.update_profile is not None:
            child.update_profile.repair_conditions.append(repair_note)
        return self._finalize(PacketOperationName.REPAIR, (packet,), child, reason="repair")

    def retire(self, packet: VerifierPacket, *, reason: str) -> OperationReport:
        child = copy.deepcopy(packet)
        if child.circulation_status is None:
            child.circulation_status = CirculationStatus()
        child.circulation_status.visibility = Visibility.RETIRED
        return self._finalize(PacketOperationName.RETIRE, (packet,), child, reason=reason)

    def quarantine(self, packet: VerifierPacket, *, reason: str) -> OperationReport:
        child = copy.deepcopy(packet)
        if child.circulation_status is None:
            child.circulation_status = CirculationStatus()
        child.circulation_status.visibility = Visibility.QUARANTINED
        return self._finalize(PacketOperationName.QUARANTINE, (packet,), child, reason=reason)

    def internalize(
        self, packet: VerifierPacket, *, translated: bool, boundary_checked: bool
    ) -> OperationReport:
        child = copy.deepcopy(packet)
        if child.circulation_status is None:
            child.circulation_status = CirculationStatus()
        if translated and boundary_checked:
            was_external = packet.circulation_status and packet.circulation_status.trust_status in {
                TrustStatus.EXTERNAL_CANDIDATE,
                TrustStatus.LOW_TRUST,
                TrustStatus.ADVERSARIAL,
                TrustStatus.UNKNOWN,
            }
            quarantine_first = packet.circulation_status and (
                packet.circulation_status.visibility == Visibility.QUARANTINED
                or packet.circulation_status.local_internalization_status.startswith("quarantined")
            )
            has_translation_record = bool(
                child.circulation_status.translation_residual_refs
                or (child.residual_hooks and child.residual_hooks.unresolved_residual_refs)
            )
            if was_external and (not quarantine_first or not has_translation_record):
                child.circulation_status.visibility = Visibility.QUARANTINED
                residual = ResidualRecord(
                    kind=ResidualKind.TRANSLATION_RESIDUAL,
                    origin=packet.packet_id,
                    scope=("internalization", "quarantine_first"),
                    obligation=(
                        "External packet requires quarantine-first translation residual handling"
                    ),
                    exposure="blocks_support",
                )
                child.residual_obligations.append(residual)
                child.circulation_status.translation_residual_refs.append(residual.residual_id)
                return self._finalize(
                    PacketOperationName.INTERNALIZE,
                    (packet,),
                    child,
                    reason="internalize",
                    extra_residuals=[residual],
                    boundary_checked=False,
                )
            child.circulation_status.trust_status = TrustStatus.LOCAL
            child.circulation_status.visibility = Visibility.PRIVATE
            child.circulation_status.local_internalization_status = "internalized"
        else:
            child.circulation_status.visibility = Visibility.QUARANTINED
            residual = ResidualRecord(
                kind=ResidualKind.TRANSLATION_RESIDUAL,
                origin=packet.packet_id,
                scope=("internalization",),
                obligation=(
                    "External packet must be translated and boundary-checked before internalization"
                ),
                exposure="blocks_support",
            )
            child.residual_obligations.append(residual)
            return self._finalize(
                PacketOperationName.INTERNALIZE,
                (packet,),
                child,
                reason="internalize",
                extra_residuals=[residual],
                boundary_checked=boundary_checked,
            )
        return self._finalize(
            PacketOperationName.INTERNALIZE,
            (packet,),
            child,
            reason="internalize",
            boundary_checked=boundary_checked,
        )

    def redact(self, packet: VerifierPacket, *, fields: tuple[str, ...]) -> OperationReport:
        child = copy.deepcopy(packet)
        core_relevant = tuple(field for field in fields if field in REQUIRED_CORE_FIELDS)
        for field_name in fields:
            if field_name in child.extension:
                del child.extension[field_name]
        exposure = "blocks_support" if core_relevant else "informational"
        residual = ResidualRecord(
            kind=ResidualKind.REDACTION_RESIDUAL,
            origin=packet.packet_id,
            scope=fields,
            obligation="Redaction preserves provenance, authority loss, and residual consequence",
            exposure=exposure,
            payload={"core_relevant_fields": list(core_relevant)},
        )
        child.residual_obligations.append(residual)
        if child.circulation_status is not None:
            child.circulation_status.redaction_residual_refs.append(residual.residual_id)
        return self._finalize(
            PacketOperationName.REDACT,
            (packet,),
            child,
            reason="redact",
            extra_residuals=[residual],
            boundary_checked=not core_relevant,
        )

    def _finalize(
        self,
        operation: PacketOperationName,
        inputs: tuple[VerifierPacket, ...],
        output: VerifierPacket,
        *,
        reason: str,
        extra_residuals: list[ResidualRecord] | None = None,
        boundary_checked: bool = True,
    ) -> OperationReport:
        residuals = extra_residuals or []
        event_refs: list[str] = []
        for residual in residuals:
            event = self.ledger.add(residual, justification=reason)
            event_refs.append(event.event_id)
        core = self._check_core_monotonicity(inputs, output)
        residual_totality = (
            pass_result("ResidualTotality")
            if residuals or not output.missing_core_fields()
            else residual_result(
                "ResidualTotality",
                FailureCode.MISSING_REQUIRED_CORE,
            )
        )
        boundary = (
            pass_result("BoundarySafety")
            if boundary_checked
            else residual_result(
                "BoundarySafety",
                FailureCode.BOUNDARY_UNCHECKED,
                residual_refs=tuple(res.residual_id for res in residuals),
            )
        )
        lineage = self._check_lineage_laundering(inputs, output)
        schema_risk = self._check_schema_overclosure_risk(output)
        admissibility = self._check_operation_admissibility(
            core=core,
            residual_totality=residual_totality,
            boundary=boundary,
            lineage=lineage,
            schema_risk=schema_risk,
        )
        return OperationReport(
            operation=operation,
            input_packet_ids=tuple(packet.packet_id for packet in inputs),
            output_packet=output,
            admissibility=admissibility,
            core_monotonicity=core,
            residual_totality=residual_totality,
            boundary_safety=boundary,
            schema_overclosure_risk=schema_risk,
            lineage_laundering=lineage,
            ledger_event_refs=tuple(event_refs),
            residual_refs=tuple(res.residual_id for res in residuals),
        )

    def _check_core_monotonicity(
        self,
        inputs: tuple[VerifierPacket, ...],
        output: VerifierPacket,
    ) -> CheckResult:
        inherited_residuals = {
            residual.residual_id for packet in inputs for residual in packet.residual_obligations
        }
        output_residuals = {residual.residual_id for residual in output.residual_obligations}
        if inherited_residuals and not inherited_residuals.issubset(output_residuals):
            return residual_result(
                "CoreMonotonicity",
                FailureCode.MIGRATION_LOSS,
                suggested_repair_hooks=("preserve_or_residualize_inherited_residuals",),
            )
        return pass_result("CoreMonotonicity")

    def _check_operation_admissibility(
        self,
        *,
        core: CheckResult,
        residual_totality: CheckResult,
        boundary: CheckResult,
        lineage: CheckResult,
        schema_risk: CheckResult,
    ) -> CheckResult:
        checks = (core, residual_totality, boundary, lineage, schema_risk)
        if all(check.passed for check in checks):
            return pass_result("OperationAdmissibility")
        residual_refs = tuple(ref for check in checks for ref in check.residual_refs)
        failure_codes = tuple(code for check in checks for code in check.failure_codes) or (
            FailureCode.MIGRATION_LOSS,
        )
        if any(check.support_blocking_failures for check in checks):
            return fail_result(
                "OperationAdmissibility",
                *failure_codes,
                residual_refs=residual_refs,
                suggested_repair_hooks=("preserve_core_residuals_boundaries_and_lineage",),
            )
        return residual_result(
            "OperationAdmissibility",
            *failure_codes,
            residual_refs=residual_refs,
            suggested_repair_hooks=("residualize_operation_invariant_loss",),
        )

    def _check_lineage_laundering(
        self, inputs: tuple[VerifierPacket, ...], output: VerifierPacket
    ) -> CheckResult:
        if output.origin is None:
            return residual_result("LineageLaundering", FailureCode.MIGRATION_LOSS)
        required = {packet.packet_id for packet in inputs}
        visible = set(output.origin.lineage)
        if len(inputs) > 1 and not required.issubset(visible):
            return residual_result(
                "LineageLaundering",
                FailureCode.MIGRATION_LOSS,
                suggested_repair_hooks=("preserve_input_packet_lineage",),
            )
        return pass_result("LineageLaundering")

    def _check_schema_overclosure_risk(self, output: VerifierPacket) -> CheckResult:
        if output.extension.get("schema_overclosure_exposure") == "unresolved":
            return residual_result(
                "SchemaOverclosureRisk",
                FailureCode.SCHEMA_OVERCLOSURE,
                suggested_repair_hooks=("schema_repair", "schema_fork", "local_extension"),
            )
        return pass_result("SchemaOverclosureRisk")
