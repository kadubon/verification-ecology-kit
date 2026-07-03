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
    live_classes: dict[str, int] = {}
    inert_classes: dict[str, int] = {}
    hoarded_classes: dict[str, int] = {}
    archived_only_classes: dict[str, int] = {}
    authority_blocking_classes: dict[str, int] = {}
    for residual in state.residual_ledger.residuals.values():
        class_name = residual.route.route_type.value if residual.route else "unrouted"
        if residual.status != LedgerStatus.ACTIVE:
            passed.append(f"{residual.residual_id}:inactive_disposition")
            archived_only_classes[class_name] = archived_only_classes.get(class_name, 0) + 1
            continue
        result = check_residual_liveness(residual)
        if result.passed:
            passed.append(f"{residual.residual_id}:live")
            live_classes[class_name] = live_classes.get(class_name, 0) + 1
            if residual.route and residual.route.authority_effect == "blocks_authority":
                authority_blocking_classes[class_name] = (
                    authority_blocking_classes.get(class_name, 0) + 1
                )
        else:
            residualized.extend(code.value for code in result.failure_codes)
            inert_classes[class_name] = inert_classes.get(class_name, 0) + 1
            if residual.route is None or not residual.route.active_follow_through:
                hoarded_classes[class_name] = hoarded_classes.get(class_name, 0) + 1
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
        passed_checks=[
            *passed,
            f"live_classes:{live_classes}",
            f"inert_classes:{inert_classes}",
            f"hoarded_classes:{hoarded_classes}",
            f"archived_only_classes:{archived_only_classes}",
            f"authority_blocking_classes:{authority_blocking_classes}",
        ],
        residualized_failures=residualized,
    ).finalize()
