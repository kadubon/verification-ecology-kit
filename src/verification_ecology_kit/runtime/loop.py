"""Runtime loop primitives."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.digest import DigestPolicy
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import OriginKind, ResidualKind
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.ports.generator import PacketGenerator
from verification_ecology_kit.result import CheckOutcome, CheckResult


@dataclass
class DefaultPacketGenerator(PacketGenerator):
    def from_residual(self, residual: ResidualRecord) -> list[VerifierPacket]:
        packet = VerifierPacket.minimal(created_from=OriginKind.RESIDUAL)
        assert packet.origin is not None
        assert packet.scope is not None
        assert packet.update_profile is not None
        packet.origin.traces.append(residual.residual_id)
        packet.scope.applies_to.extend(residual.scope)
        packet.residual_obligations.append(residual)
        packet.update_profile.revalidation_triggers.append("residual_recheck")
        return [packet]


@dataclass
class RuntimeStageResult:
    stage_name: str
    packet_id: str
    check_result: CheckResult
    notes: list[str] = field(default_factory=list)
    decision: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    residual_refs: list[str] = field(default_factory=list)
    authority_effect: str = ""
    report_digest: str = ""

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "stage_name": self.stage_name,
            "packet_id": self.packet_id,
            "check_result": self.check_result.to_dict(),
            "decision": self.decision or self.check_result.result.value,
            "evidence_refs": self.evidence_refs or list(self.check_result.evidence_refs),
            "residual_refs": self.residual_refs or list(self.check_result.residual_refs),
            "authority_effect": self.authority_effect or self._authority_effect(),
            "notes": self.notes,
            "report_digest": "",
        }
        payload["report_digest"] = self.report_digest or DigestPolicy().digest_json(payload).value
        return payload

    def _authority_effect(self) -> str:
        if self.check_result.result == CheckOutcome.PASS:
            return "none"
        if self.check_result.support_blocking_failures:
            return "blocks_authority"
        if self.check_result.result == CheckOutcome.RESIDUALIZE:
            return "residualize"
        return "blocks_support"


RuntimeStage = RuntimeStageResult


@dataclass
class RuntimeReport:
    generated_packets: list[str] = field(default_factory=list)
    generated_from_residuals: list[str] = field(default_factory=list)
    inherited_residual_refs: list[str] = field(default_factory=list)
    inherited_boundary_refs: list[str] = field(default_factory=list)
    anti_overclosure_gaps: list[str] = field(default_factory=list)
    counter_packet_obligations: list[str] = field(default_factory=list)
    stages: list[RuntimeStageResult] = field(default_factory=list)
    quarantine_decisions: list[dict[str, object]] = field(default_factory=list)
    reachability_checks: list[dict[str, object]] = field(default_factory=list)
    schema_checks: list[dict[str, object]] = field(default_factory=list)
    lineage_checks: list[dict[str, object]] = field(default_factory=list)
    repair_or_retire_decisions: list[dict[str, object]] = field(default_factory=list)
    frontier_updates: list[dict[str, object]] = field(default_factory=list)
    aperture_updates: list[dict[str, object]] = field(default_factory=list)
    quarantined_packets: list[str] = field(default_factory=list)
    residuals_routed: list[str] = field(default_factory=list)
    aperture_debts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    report_digest: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_packets": self.generated_packets,
            "generated_from_residuals": self.generated_from_residuals,
            "inherited_residual_refs": self.inherited_residual_refs,
            "inherited_boundary_refs": self.inherited_boundary_refs,
            "anti_overclosure_gaps": self.anti_overclosure_gaps,
            "counter_packet_obligations": self.counter_packet_obligations,
            "stages": [stage.to_dict() for stage in self.stages],
            "quarantine_decisions": self.quarantine_decisions,
            "reachability_checks": self.reachability_checks,
            "schema_checks": self.schema_checks,
            "lineage_checks": self.lineage_checks,
            "repair_or_retire_decisions": self.repair_or_retire_decisions,
            "frontier_updates": self.frontier_updates,
            "aperture_updates": self.aperture_updates,
            "quarantined_packets": self.quarantined_packets,
            "residuals_routed": self.residuals_routed,
            "aperture_debts": self.aperture_debts,
            "notes": self.notes,
            "report_digest": self.report_digest,
        }

    def finalize(self) -> RuntimeReport:
        payload = self.to_dict()
        payload["report_digest"] = ""
        self.report_digest = DigestPolicy().digest_json(payload).value
        return self


def residual_from_history_event(
    event_type: str, payload: dict[str, object], event_id: str
) -> ResidualRecord | None:
    if event_type not in {"unknown", "failure", "success", "contrast", "external_packet"}:
        return None
    origin_kind = {
        "unknown": ResidualKind.UNRESOLVED,
        "failure": ResidualKind.UNRESOLVED,
        "success": ResidualKind.DELIBERATELY_PRESERVED,
        "contrast": ResidualKind.UNRESOLVED,
        "external_packet": ResidualKind.UNTRANSLATED,
    }[event_type]
    return ResidualRecord(
        kind=origin_kind,
        origin=event_id,
        scope=(event_type,),
        obligation=f"Generate or preserve verifier material from history event: {event_type}",
        payload={"history_payload": payload},
    )
