"""Runtime loop primitives."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.digest import DigestPolicy
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import OriginKind, ResidualKind
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.ports.generator import PacketGenerator


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
class RuntimeReport:
    generated_packets: list[str] = field(default_factory=list)
    quarantined_packets: list[str] = field(default_factory=list)
    residuals_routed: list[str] = field(default_factory=list)
    aperture_debts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    report_digest: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_packets": self.generated_packets,
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
