"""Typed check results used by validators, audits, and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class CheckOutcome(StrEnum):
    PASS = "pass"  # noqa: S105  # nosec B105
    FAIL = "fail"
    RESIDUALIZE = "residualize"
    QUARANTINE = "quarantine"
    NOT_CHECKED = "not_checked"


class ConformanceDecision(StrEnum):
    ACCEPT = "accept"
    ACCEPT_WITH_RESIDUALS = "accept_with_residuals"
    QUARANTINE = "quarantine"
    REJECT = "reject"


class FailureCode(StrEnum):
    SCHEMA_INVALID = "schema_invalid"
    DUPLICATE_MEMBER = "duplicate_member"
    INVALID_UNICODE = "invalid_unicode"
    NON_INTEROPERABLE_NUMBER = "non_interoperable_number"
    UNSUPPORTED_DIGEST_ALGORITHM = "unsupported_digest_algorithm"
    DIGEST_MISMATCH = "digest_mismatch"
    CANONICALIZATION_DRIFT = "canonicalization_drift"
    UNSUPPORTED_SCHEMA_VERSION = "unsupported_schema_version"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    REFERENCE_BROKEN = "reference_broken"
    STATUS_BLOCKS_SUPPORT = "status_blocks_support"
    JUDGMENT_INVALID = "judgment_invalid"
    RESIDUAL_NOT_LIVE = "residual_not_live"
    SOUNDGAP_NOT_LIVE = "soundgap_not_live"
    EXPIRED_COUNTEREXAMPLE_CLOSURE = "expired_counterexample_closure"
    AUTHORITY_MISMATCH = "authority_mismatch"
    MISSING_REQUIRED_CORE = "missing_required_core"
    MISSING_COUNTER_PACKET = "missing_counter_packet"
    BOUNDARY_UNCHECKED = "boundary_unchecked"
    OVERCLOSURE_RISK = "overclosure_risk"
    SCHEMA_OVERCLOSURE = "schema_overclosure"
    LOCAL_INFORMATION_LEAK = "local_information_leak"
    SECRET_LEAK = "secret_leak"  # noqa: S105  # nosec B105
    PACKAGE_CONTENT_LEAK = "package_content_leak"
    MIGRATION_LOSS = "migration_loss"
    STALE_NON_AUTHORITY_EVIDENCE = "stale_non_authority_evidence"
    UNSUPPORTED_DASHBOARD_FIELD = "unsupported_dashboard_field"


SUPPORT_BLOCKING_FAILURES: frozenset[FailureCode] = frozenset(
    {
        FailureCode.UNRESOLVED_REFERENCE,
        FailureCode.AMBIGUOUS_REFERENCE,
        FailureCode.REFERENCE_BROKEN,
        FailureCode.DIGEST_MISMATCH,
        FailureCode.STATUS_BLOCKS_SUPPORT,
        FailureCode.SOUNDGAP_NOT_LIVE,
        FailureCode.EXPIRED_COUNTEREXAMPLE_CLOSURE,
        FailureCode.AUTHORITY_MISMATCH,
        FailureCode.JUDGMENT_INVALID,
        FailureCode.MISSING_REQUIRED_CORE,
        FailureCode.BOUNDARY_UNCHECKED,
    }
)

RESIDUALIZABLE_FAILURES: frozenset[FailureCode] = frozenset(
    {
        FailureCode.NON_INTEROPERABLE_NUMBER,
        FailureCode.CANONICALIZATION_DRIFT,
        FailureCode.MIGRATION_LOSS,
        FailureCode.STALE_NON_AUTHORITY_EVIDENCE,
        FailureCode.UNSUPPORTED_DASHBOARD_FIELD,
        FailureCode.MISSING_COUNTER_PACKET,
        FailureCode.OVERCLOSURE_RISK,
        FailureCode.SCHEMA_OVERCLOSURE,
        FailureCode.RESIDUAL_NOT_LIVE,
    }
)

QUARANTINE_FAILURES: frozenset[FailureCode] = frozenset(
    {
        FailureCode.SECRET_LEAK,
        FailureCode.LOCAL_INFORMATION_LEAK,
        FailureCode.PACKAGE_CONTENT_LEAK,
        FailureCode.INVALID_UNICODE,
        FailureCode.DUPLICATE_MEMBER,
    }
)


@dataclass(frozen=True)
class CheckResult:
    check_name: str
    result: CheckOutcome
    failure_codes: tuple[FailureCode, ...] = ()
    residual_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    suggested_repair_hooks: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.result == CheckOutcome.PASS

    @property
    def support_blocking_failures(self) -> tuple[FailureCode, ...]:
        return tuple(code for code in self.failure_codes if code in SUPPORT_BLOCKING_FAILURES)

    @property
    def residualizable_failures(self) -> tuple[FailureCode, ...]:
        return tuple(code for code in self.failure_codes if code in RESIDUALIZABLE_FAILURES)

    @property
    def quarantine_triggers(self) -> tuple[FailureCode, ...]:
        return tuple(code for code in self.failure_codes if code in QUARANTINE_FAILURES)

    def to_dict(self) -> dict[str, object]:
        return {
            "check_name": self.check_name,
            "result": self.result.value,
            "failure_codes": [code.value for code in self.failure_codes],
            "residual_refs": list(self.residual_refs),
            "evidence_refs": list(self.evidence_refs),
            "suggested_repair_hooks": list(self.suggested_repair_hooks),
            "provenance": list(self.provenance),
        }


def pass_result(check_name: str, *, evidence_refs: tuple[str, ...] = ()) -> CheckResult:
    return CheckResult(check_name=check_name, result=CheckOutcome.PASS, evidence_refs=evidence_refs)


def fail_result(
    check_name: str,
    *failure_codes: FailureCode,
    residual_refs: tuple[str, ...] = (),
    suggested_repair_hooks: tuple[str, ...] = (),
) -> CheckResult:
    return CheckResult(
        check_name=check_name,
        result=CheckOutcome.FAIL,
        failure_codes=tuple(failure_codes),
        residual_refs=residual_refs,
        suggested_repair_hooks=suggested_repair_hooks,
    )


def residual_result(
    check_name: str,
    *failure_codes: FailureCode,
    residual_refs: tuple[str, ...] = (),
    suggested_repair_hooks: tuple[str, ...] = (),
) -> CheckResult:
    return CheckResult(
        check_name=check_name,
        result=CheckOutcome.RESIDUALIZE,
        failure_codes=tuple(failure_codes),
        residual_refs=residual_refs,
        suggested_repair_hooks=suggested_repair_hooks,
    )


@dataclass
class ConformanceReport:
    profile: str
    decision: ConformanceDecision
    ordered_check_results: list[CheckResult]
    support_blocking_failures: list[FailureCode] = field(default_factory=list)
    residualized_failures: list[FailureCode] = field(default_factory=list)
    quarantine_triggers: list[FailureCode] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    suggested_repair_hooks: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    checked_input_digest: str | None = None
    report_digest: str | None = None
    semantic_report: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "profile": self.profile,
            "decision": self.decision.value,
            "ordered_check_results": [result.to_dict() for result in self.ordered_check_results],
            "support_blocking_failures": [code.value for code in self.support_blocking_failures],
            "residualized_failures": [code.value for code in self.residualized_failures],
            "quarantine_triggers": [code.value for code in self.quarantine_triggers],
            "evidence_refs": self.evidence_refs,
            "suggested_repair_hooks": self.suggested_repair_hooks,
            "provenance": self.provenance,
            "checked_input_digest": self.checked_input_digest,
            "report_digest": self.report_digest,
            "semantic_report": self.semantic_report,
        }

    @classmethod
    def from_results(
        cls,
        *,
        profile: str,
        ordered_check_results: list[CheckResult],
        checked_input_digest: str | None = None,
    ) -> ConformanceReport:
        support_blocking: list[FailureCode] = []
        residualized: list[FailureCode] = []
        quarantine: list[FailureCode] = []
        repairs: list[str] = []
        evidence: list[str] = []
        for result in ordered_check_results:
            support_blocking.extend(result.support_blocking_failures)
            residualized.extend(result.residualizable_failures)
            quarantine.extend(result.quarantine_triggers)
            repairs.extend(result.suggested_repair_hooks)
            evidence.extend(result.evidence_refs)
        if support_blocking:
            decision = ConformanceDecision.REJECT
        elif quarantine:
            decision = ConformanceDecision.QUARANTINE
        elif residualized or any(
            r.result == CheckOutcome.RESIDUALIZE for r in ordered_check_results
        ):
            decision = ConformanceDecision.ACCEPT_WITH_RESIDUALS
        elif all(r.passed for r in ordered_check_results):
            decision = ConformanceDecision.ACCEPT
        else:
            decision = ConformanceDecision.REJECT
        return cls(
            profile=profile,
            decision=decision,
            ordered_check_results=ordered_check_results,
            support_blocking_failures=list(dict.fromkeys(support_blocking)),
            residualized_failures=list(dict.fromkeys(residualized)),
            quarantine_triggers=list(dict.fromkeys(quarantine)),
            evidence_refs=list(dict.fromkeys(evidence)),
            suggested_repair_hooks=list(dict.fromkeys(repairs)),
            checked_input_digest=checked_input_digest,
        )
