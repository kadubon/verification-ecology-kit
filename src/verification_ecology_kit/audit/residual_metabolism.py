"""Residual metabolism audit."""

from __future__ import annotations

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.records import LedgerStatus
from verification_ecology_kit.model.residuals import check_residual_liveness


def audit_residual_metabolism(state: VerifierEcologyState) -> AuditReport:
    findings: list[AuditFinding] = []
    passed: list[str] = []
    residualized: list[str] = []
    for residual in state.residual_ledger.residuals.values():
        if residual.status != LedgerStatus.ACTIVE:
            passed.append(f"{residual.residual_id}:inactive_disposition")
            continue
        result = check_residual_liveness(residual)
        if result.passed:
            passed.append(f"{residual.residual_id}:live")
        else:
            residualized.extend(code.value for code in result.failure_codes)
            findings.append(
                AuditFinding(
                    code="liveness_debt",
                    message=f"Residual {residual.residual_id} is active without a live route",
                    evidence_refs=(residual.residual_id,),
                    suggested_repair_hooks=("route_residual", "retire_with_reason", "quarantine"),
                )
            )
    decision = "pass" if not findings else "residualize"
    return AuditReport(
        audit_name="residual-metabolism",
        decision=decision,
        findings=findings,
        passed_checks=passed,
        residualized_failures=residualized,
    ).finalize()
