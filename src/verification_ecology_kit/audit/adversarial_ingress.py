"""Adversarial packet ingress audit."""

from __future__ import annotations

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import TrustStatus, Visibility


def audit_adversarial_ingress(packet: VerifierPacket) -> AuditReport:
    findings: list[AuditFinding] = []
    status = packet.circulation_status
    if status is None:
        findings.append(
            AuditFinding("missing_circulation_status", "Packet has no circulation status.")
        )
    elif (
        status.trust_status in {TrustStatus.LOW_TRUST, TrustStatus.ADVERSARIAL}
        and status.visibility != Visibility.QUARANTINED
    ):
        findings.append(
            AuditFinding(
                "low_trust_not_quarantined",
                "Low-trust or adversarial packet must be quarantined before internalization.",
                severity="high",
                evidence_refs=(packet.packet_id,),
                suggested_repair_hooks=("quarantine_packet",),
            )
        )
    decision = "pass" if not findings else "quarantine"
    return AuditReport("adversarial-ingress", decision, findings=findings).finalize()
