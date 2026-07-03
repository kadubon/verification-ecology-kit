"""Packet ecology audit."""

from __future__ import annotations

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport
from verification_ecology_kit.model.packets import VerifierPacket


def audit_packet_ecology(packets: list[VerifierPacket]) -> AuditReport:
    findings: list[AuditFinding] = []
    passed: list[str] = []
    residualized: list[str] = []
    blocking: list[str] = []
    for packet in packets:
        for result in packet.validate():
            if result.passed:
                passed.append(f"{packet.packet_id}:{result.check_name}")
                continue
            codes = [code.value for code in result.failure_codes]
            residualized.extend(codes)
            if result.support_blocking_failures:
                blocking.extend(code.value for code in result.support_blocking_failures)
            findings.append(
                AuditFinding(
                    code=",".join(codes) or result.check_name,
                    message=f"Packet {packet.packet_id} requires {result.check_name}",
                    evidence_refs=(packet.packet_id,),
                    suggested_repair_hooks=result.suggested_repair_hooks,
                )
            )
    decision = "pass" if not findings else "residualize"
    return AuditReport(
        audit_name="packet-ecology",
        decision=decision,
        findings=findings,
        passed_checks=passed,
        residualized_failures=residualized,
        support_blocking_failures=blocking,
    ).finalize()
