"""Default runtime policies."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import TrustStatus, Visibility


@dataclass(frozen=True)
class DefaultRuntimePolicy:
    quarantine_external: bool = True
    quarantine_low_trust: bool = True
    require_boundary_refs: bool = True

    def should_quarantine(self, packet: VerifierPacket) -> bool:
        status = packet.circulation_status
        if status is None:
            return True
        if self.quarantine_external and status.trust_status == TrustStatus.EXTERNAL_CANDIDATE:
            return True
        if self.quarantine_low_trust and status.trust_status in {
            TrustStatus.LOW_TRUST,
            TrustStatus.ADVERSARIAL,
        }:
            return True
        if status.visibility in {Visibility.REDACTED, Visibility.QUARANTINED}:
            return True
        return self.require_boundary_refs and (
            packet.boundary_refs is None
            or not (
                packet.boundary_refs.destructive_boundary_ref
                or packet.boundary_refs.narrowing_boundary_ref
                or packet.boundary_refs.reachability_certificate_refs
            )
        )
