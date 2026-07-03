"""External packet circulation and local sovereignty checks."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import TrustStatus, Visibility
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result


@dataclass(frozen=True)
class ExternalPacket:
    packet: VerifierPacket
    source_ecology: str
    received_at: str
    trust_basis: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalInternalizationResult:
    packet_id: str
    quarantine_first: bool
    translated: bool
    boundary_checked: bool
    internalized: bool
    residual_refs: tuple[str, ...] = ()


class LocalSovereignty:
    def quarantine_external(self, external: ExternalPacket) -> CheckResult:
        if external.packet.circulation_status is None:
            return residual_result("LocalSovereignty", FailureCode.MISSING_REQUIRED_CORE)
        external.packet.circulation_status.visibility = Visibility.QUARANTINED
        external.packet.circulation_status.trust_status = TrustStatus.EXTERNAL_CANDIDATE
        external.packet.circulation_status.local_internalization_status = "quarantined"
        return pass_result("LocalSovereignty", evidence_refs=(external.packet.packet_id,))

    def internalize(
        self,
        packet: VerifierPacket,
        *,
        translated: bool,
        boundary_checked: bool,
    ) -> LocalInternalizationResult:
        if packet.circulation_status is None:
            return LocalInternalizationResult(
                packet.packet_id, False, translated, boundary_checked, False
            )
        if not translated or not boundary_checked:
            packet.circulation_status.visibility = Visibility.QUARANTINED
            return LocalInternalizationResult(
                packet.packet_id, True, translated, boundary_checked, False
            )
        packet.circulation_status.trust_status = TrustStatus.LOCAL
        packet.circulation_status.local_internalization_status = "internalized"
        return LocalInternalizationResult(packet.packet_id, True, True, True, True)
