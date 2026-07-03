"""Schema-overclosure audit."""

from __future__ import annotations

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport
from verification_ecology_kit.model.overclosure import SchemaOverclosureDetector


def audit_schema_overclosure(
    *,
    schema_rejected_unknown: bool,
    suppressed_residuals: tuple[str, ...] = (),
    dashboard_hid_component_failure: bool = False,
) -> AuditReport:
    result, residuals = SchemaOverclosureDetector().detect(
        schema_rejected_unknown=schema_rejected_unknown,
        suppressed_residuals=suppressed_residuals,
        dashboard_hid_component_failure=dashboard_hid_component_failure,
    )
    findings = [
        AuditFinding(
            code=code.value,
            message="Schema behavior may suppress residuals or unknowns.",
            evidence_refs=tuple(residual.residual_id for residual in residuals),
            suggested_repair_hooks=result.suggested_repair_hooks,
        )
        for code in result.failure_codes
    ]
    return AuditReport(
        "schema-overclosure",
        "pass" if result.passed else "residualize",
        findings=findings,
    ).finalize()
