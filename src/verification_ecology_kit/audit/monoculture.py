"""Verifier monoculture audit."""

from __future__ import annotations

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport
from verification_ecology_kit.model.overclosure import VerifierMonocultureDetector


def audit_monoculture(
    *,
    origin_assumptions: list[tuple[str, ...]],
    question_forms: list[tuple[str, ...]],
    residual_filters: list[tuple[str, ...]],
    counter_packet_routes: list[tuple[str, ...]],
) -> AuditReport:
    result = VerifierMonocultureDetector().detect(
        origin_assumptions=origin_assumptions,
        question_forms=question_forms,
        residual_filters=residual_filters,
        counter_packet_routes=counter_packet_routes,
    )
    findings = [
        AuditFinding(
            code=code.value,
            message="Packet population has shared assumptions, filters, or missing counter routes.",
            suggested_repair_hooks=result.suggested_repair_hooks,
        )
        for code in result.failure_codes
    ]
    return AuditReport(
        "monoculture",
        "pass" if result.passed else "residualize",
        findings=findings,
    ).finalize()
