"""Deny-by-default authority decisions."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    LifecycleStatus,
    jsonable,
)
from verification_ecology_kit.result import (
    CheckResult,
    FailureCode,
    fail_result,
    pass_result,
    residual_result,
)

DECISION_PRECEDENCE: dict[AuthorityDecisionValue, int] = {
    AuthorityDecisionValue.DENY: 4,
    AuthorityDecisionValue.QUARANTINE: 3,
    AuthorityDecisionValue.RESIDUALIZE: 2,
    AuthorityDecisionValue.ALLOW: 1,
}


@dataclass
class AuthInputs:
    auth_inputs_ref: str
    object_id: str
    schema_version: str
    canonical_digest: Digest
    candidate_ref: str
    action: AuthorityAction
    action_scope: tuple[str, ...] = ()
    resolved_input_refs: tuple[str, ...] = ()
    support_refs: tuple[str, ...] = ()
    absence_cert_refs: tuple[str, ...] = ()
    counterexample_refs: tuple[str, ...] = ()
    soundgap_refs: tuple[str, ...] = ()
    status_view_refs: tuple[str, ...] = ()
    policy_conflict_refs: tuple[str, ...] = ()
    input_digest: Digest | None = None


@dataclass
class AuthorityDecision:
    authority_decision_id: str
    object_id: str
    schema_version: str
    canonical_digest: Digest
    lifecycle_status: LifecycleStatus
    policy_id: str
    action: AuthorityAction
    decision: AuthorityDecisionValue
    deny_by_default: bool = True
    linked_certification_records: tuple[str, ...] = ()
    auth_inputs_ref: str = ""
    required_certification_components: tuple[str, ...] = ()
    required_support_refs: tuple[str, ...] = ()
    support_judgment_refs: tuple[str, ...] = ()
    aggregate_judgment_ref: str = ""
    cex_closed_judgment_refs: tuple[str, ...] = ()
    soundgap_refs: tuple[str, ...] = ()
    scope_action_match: str = "not_checked"
    required_human_assessment_roles: tuple[str, ...] = ()
    required_tool_assessment_roles: tuple[str, ...] = ()
    rollback_hooks_required: tuple[str, ...] = ()
    expiry: str = ""
    revocation_hooks: tuple[str, ...] = ()
    tightening_conditions: tuple[str, ...] = ()
    delegation_basis: tuple[str, ...] = ()
    migration_witness_ref: str = ""
    sandbox_required: bool = False
    sandbox_status: str = "not_applicable"
    sandbox_waiver_residuals: tuple[str, ...] = ()
    residual_gates: tuple[str, ...] = ()
    ledger_event_refs: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


class AuthorityEngine:
    def aggregate(
        self,
        action: AuthorityAction,
        decisions: list[AuthorityDecision],
        *,
        required_support_refs: tuple[str, ...] = (),
        stale_or_unknown_support_refs: tuple[str, ...] = (),
        counterexample_challenged_refs: tuple[str, ...] = (),
        residual_gates_blocking: tuple[str, ...] = (),
    ) -> tuple[AuthorityDecisionValue, CheckResult]:
        active = [
            decision
            for decision in decisions
            if decision.action == action and decision.lifecycle_status == LifecycleStatus.ACTIVE
        ]
        if not active:
            return AuthorityDecisionValue.DENY, fail_result(
                "AuthorityOK",
                FailureCode.AUTHORITY_MISMATCH,
                suggested_repair_hooks=("create_active_authority_decision",),
            )
        if (
            stale_or_unknown_support_refs
            or counterexample_challenged_refs
            or residual_gates_blocking
        ):
            return AuthorityDecisionValue.DENY, fail_result(
                "AuthorityOK",
                FailureCode.AUTHORITY_MISMATCH,
                residual_refs=stale_or_unknown_support_refs
                + counterexample_challenged_refs
                + residual_gates_blocking,
            )
        best = max(active, key=lambda item: DECISION_PRECEDENCE[item.decision])
        if best.decision != AuthorityDecisionValue.ALLOW:
            if best.decision == AuthorityDecisionValue.RESIDUALIZE:
                return best.decision, residual_result(
                    "AuthorityOK",
                    FailureCode.AUTHORITY_MISMATCH,
                    residual_refs=best.residual_gates,
                )
            return best.decision, fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
        missing_support = set(required_support_refs) - set(best.required_support_refs)
        if missing_support:
            return AuthorityDecisionValue.DENY, fail_result(
                "AuthorityOK",
                FailureCode.AUTHORITY_MISMATCH,
                suggested_repair_hooks=tuple(
                    f"add_required_support:{ref}" for ref in sorted(missing_support)
                ),
            )
        if best.sandbox_required and best.sandbox_status != "active":
            return AuthorityDecisionValue.DENY, fail_result(
                "AuthorityOK", FailureCode.AUTHORITY_MISMATCH
            )
        return AuthorityDecisionValue.ALLOW, pass_result(
            "AuthorityOK",
            evidence_refs=(best.authority_decision_id,),
        )
