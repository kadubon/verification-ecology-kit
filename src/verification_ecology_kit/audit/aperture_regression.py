"""Aperture regression audit."""

from __future__ import annotations

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport
from verification_ecology_kit.model.aperture import Aperture


def audit_aperture_regression(before: Aperture, after: Aperture) -> AuditReport:
    findings: list[AuditFinding] = []
    if before.strict_capacity_leq(after):
        return AuditReport(
            audit_name="aperture-regression",
            decision="pass",
            passed_checks=["strict_capacity_comparison"],
        ).finalize()
    if before.accountable_loss_leq(after):
        findings.append(
            AuditFinding(
                code="accountable_aperture_loss",
                message="Feasible aperture decreased, but the loss is residualized.",
                severity="low",
                suggested_repair_hooks=("review_aperture_debt",),
            )
        )
        return AuditReport(
            audit_name="aperture-regression",
            decision="residualize",
            findings=findings,
            residualized_failures=["aperture_debt"],
        ).finalize()
    findings.append(
        AuditFinding(
            code="silent_aperture_loss",
            message="Feasible aperture decreased without a residual obligation.",
            severity="high",
            suggested_repair_hooks=("create_aperture_debt_residual",),
        )
    )
    return AuditReport(
        audit_name="aperture-regression",
        decision="reject",
        findings=findings,
        support_blocking_failures=["aperture_debt"],
    ).finalize()
