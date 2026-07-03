"""Verifier packets and packet validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.records import (
    OriginKind,
    ResidualKind,
    TrustStatus,
    Visibility,
    jsonable,
)
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result

REQUIRED_CORE_FIELDS: tuple[str, ...] = (
    "origin",
    "scope",
    "transformation_class",
    "verifier_procedure",
    "certification_condition",
    "boundary_refs",
    "residual_hooks",
    "update_profile",
    "circulation_status",
)


@dataclass
class PacketOrigin:
    created_from: OriginKind
    traces: list[str] = field(default_factory=list)
    lineage: list[str] = field(default_factory=list)
    unresolved_origin_residuals: list[str] = field(default_factory=list)


@dataclass
class PacketScope:
    applies_to: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    unvalidated_assumptions: list[str] = field(default_factory=list)
    known_misuse_contexts: list[str] = field(default_factory=list)
    known_invalid_scopes: list[str] = field(default_factory=list)


@dataclass
class TransformationClass:
    allowed: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    transfer_conditions: list[str] = field(default_factory=list)
    self_modification_roles: list[str] = field(default_factory=list)


@dataclass
class VerifierProcedure:
    steps: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    proof_obligations: list[str] = field(default_factory=list)
    statistical_methods: list[str] = field(default_factory=list)
    stochastic_methods: list[str] = field(default_factory=list)
    tool_dependencies: list[str] = field(default_factory=list)
    evaluator_versions: list[str] = field(default_factory=list)


@dataclass
class CertificationCondition:
    pass_conditions: list[str] = field(default_factory=list)
    fail_conditions: list[str] = field(default_factory=list)
    quarantine_conditions: list[str] = field(default_factory=list)
    residualization_conditions: list[str] = field(default_factory=list)
    promotion_conditions: list[str] = field(default_factory=list)


@dataclass
class BoundaryRefs:
    destructive_boundary_ref: str = ""
    narrowing_boundary_ref: str = ""
    reachability_certificate_refs: list[str] = field(default_factory=list)


@dataclass
class ResidualHooks:
    unresolved_residual_refs: list[str] = field(default_factory=list)
    missing_core_fields: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    conflict_residual_refs: list[str] = field(default_factory=list)
    merge_loss_residual_refs: list[str] = field(default_factory=list)
    redaction_residual_refs: list[str] = field(default_factory=list)


@dataclass
class UpdateProfile:
    repair_conditions: list[str] = field(default_factory=list)
    retirement_conditions: list[str] = field(default_factory=list)
    revalidation_triggers: list[str] = field(default_factory=list)
    scope_drift_triggers: list[str] = field(default_factory=list)
    contamination_triggers: list[str] = field(default_factory=list)
    rollback_hooks: list[str] = field(default_factory=list)


@dataclass
class CirculationStatus:
    visibility: Visibility = Visibility.PRIVATE
    trust_status: TrustStatus = TrustStatus.LOCAL
    local_internalization_status: str = "local"


@dataclass
class VerifierPacket:
    origin: PacketOrigin | None
    scope: PacketScope | None
    transformation_class: TransformationClass | None
    verifier_procedure: VerifierProcedure | None
    certification_condition: CertificationCondition | None
    boundary_refs: BoundaryRefs | None
    residual_hooks: ResidualHooks | None
    update_profile: UpdateProfile | None
    circulation_status: CirculationStatus | None
    packet_id: str = field(default_factory=lambda: new_id("pkt"))
    question_form: dict[str, Any] = field(default_factory=dict)
    extension: dict[str, Any] = field(default_factory=dict)
    residual_obligations: list[ResidualRecord] = field(default_factory=list)
    counter_packet_refs: list[str] = field(default_factory=list)

    @classmethod
    def minimal(
        cls, *, created_from: OriginKind = OriginKind.HUMAN_SPECIFICATION
    ) -> VerifierPacket:
        packet = cls(
            origin=PacketOrigin(created_from=created_from),
            scope=PacketScope(),
            transformation_class=TransformationClass(),
            verifier_procedure=VerifierProcedure(),
            certification_condition=CertificationCondition(),
            boundary_refs=BoundaryRefs(),
            residual_hooks=ResidualHooks(),
            update_profile=UpdateProfile(),
            circulation_status=CirculationStatus(),
        )
        packet.ensure_core_accountability()
        return packet

    @classmethod
    def from_external_candidate(cls) -> VerifierPacket:
        packet = cls.minimal(created_from=OriginKind.EXTERNAL_PACKET)
        packet.circulation_status = CirculationStatus(
            visibility=Visibility.QUARANTINED,
            trust_status=TrustStatus.EXTERNAL_CANDIDATE,
            local_internalization_status="quarantined_pending_translation",
        )
        return packet

    def missing_core_fields(self) -> list[str]:
        missing: list[str] = []
        for field_name in REQUIRED_CORE_FIELDS:
            if getattr(self, field_name) is None:
                missing.append(field_name)
        return missing

    def ensure_core_accountability(self) -> list[ResidualRecord]:
        missing = self.missing_core_fields()
        if self.residual_hooks is None:
            self.residual_hooks = ResidualHooks()
        created: list[ResidualRecord] = []
        for field_name in missing:
            if field_name not in self.residual_hooks.missing_core_fields:
                self.residual_hooks.missing_core_fields.append(field_name)
            if not any(
                residual.kind == ResidualKind.MISSING and field_name in residual.scope
                for residual in self.residual_obligations
            ):
                residual = ResidualRecord(
                    kind=ResidualKind.MISSING,
                    origin=self.packet_id,
                    scope=(field_name,),
                    obligation=f"Provide or residualize missing packet core field: {field_name}",
                    exposure="blocks_support",
                )
                self.residual_obligations.append(residual)
                created.append(residual)
        return created

    def validate(self) -> list[CheckResult]:
        created = self.ensure_core_accountability()
        missing = self.missing_core_fields()
        results: list[CheckResult] = []
        if missing:
            results.append(
                residual_result(
                    "PacketCoreAccountability",
                    FailureCode.MISSING_REQUIRED_CORE,
                    residual_refs=tuple(residual.residual_id for residual in created),
                    suggested_repair_hooks=("fill_core_field_or_keep_live_residual",),
                )
            )
        else:
            results.append(pass_result("PacketCoreAccountability", evidence_refs=(self.packet_id,)))
        if not self.counter_packet_refs:
            residual = ResidualRecord(
                kind=ResidualKind.MISSING_COUNTER,
                origin=self.packet_id,
                scope=("counter_packet",),
                obligation=(
                    "Attach counter-packet, boundary tester, or keep missing-counter residual live"
                ),
                exposure="residualize",
            )
            self.residual_obligations.append(residual)
            if self.residual_hooks is None:
                self.residual_hooks = ResidualHooks()
            self.residual_hooks.unresolved_residual_refs.append(residual.residual_id)
            results.append(
                residual_result(
                    "CounterPacketAdequacy",
                    FailureCode.MISSING_COUNTER_PACKET,
                    residual_refs=(residual.residual_id,),
                )
            )
        else:
            results.append(
                pass_result("CounterPacketAdequacy", evidence_refs=tuple(self.counter_packet_refs))
            )
        if self.boundary_refs and (
            self.boundary_refs.destructive_boundary_ref or self.boundary_refs.narrowing_boundary_ref
        ):
            results.append(pass_result("BoundaryRefsPresent"))
        else:
            results.append(
                residual_result(
                    "BoundaryRefsPresent",
                    FailureCode.BOUNDARY_UNCHECKED,
                    residual_refs=tuple(res.residual_id for res in self.residual_obligations),
                    suggested_repair_hooks=("attach_boundary_record_or_reachability_residual",),
                )
            )
        return results

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


CoreAccountablePacket = VerifierPacket


@dataclass
class CounterPacketFinding:
    target_packet_id: str
    issue: str
    residual_kind: ResidualKind
    authority_effect: str = "blocks_support"


@dataclass
class CounterPacket(VerifierPacket):
    target_packet_id: str = ""
    inspection_roles: list[str] = field(default_factory=list)

    def inspect_target(self, target: VerifierPacket) -> list[CounterPacketFinding]:
        findings: list[CounterPacketFinding] = []
        if target.residual_hooks is None or not target.residual_obligations:
            findings.append(
                CounterPacketFinding(
                    target.packet_id,
                    "residual deletion or missing residual hooks",
                    ResidualKind.MISSING_COUNTER,
                )
            )
        if target.boundary_refs is None or not (
            target.boundary_refs.destructive_boundary_ref
            or target.boundary_refs.narrowing_boundary_ref
            or target.boundary_refs.reachability_certificate_refs
        ):
            findings.append(
                CounterPacketFinding(
                    target.packet_id,
                    "boundary bypass or missing boundary record",
                    ResidualKind.UNEXCLUDED,
                )
            )
        if target.scope and target.scope.unvalidated_assumptions:
            findings.append(
                CounterPacketFinding(
                    target.packet_id,
                    "scope inflation through unvalidated assumptions",
                    ResidualKind.UNRESOLVED,
                )
            )
        return findings


@dataclass
class BoundaryTesterPacket(CounterPacket):
    destructive_tests: list[str] = field(default_factory=list)
    narrowing_tests: list[str] = field(default_factory=list)
