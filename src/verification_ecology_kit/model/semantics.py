"""Operational semantic profile reporting for VET bundles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from verification_ecology_kit.model.records import ConformanceProfile, jsonable
from verification_ecology_kit.result import CheckOutcome, CheckResult


class SemanticLevel(StrEnum):
    SCHEMA = "schema"
    RECORD = "record"
    EVIDENCE = "evidence"
    SUPPORT = "support"
    AUTHORITY = "authority"
    ECOLOGY = "ecology"


class SupportEligibility(StrEnum):
    ELIGIBLE = "eligible"
    ELIGIBLE_WITH_RESIDUALS = "eligible_with_residuals"
    BLOCKED = "blocked"
    NOT_CHECKED = "not_checked"


class AuthorityEligibility(StrEnum):
    ALLOWABLE = "allowable"
    ALLOWABLE_WITH_RESIDUALS = "allowable_with_residuals"
    BLOCKED = "blocked"
    NOT_CHECKED = "not_checked"


class EcologyEligibility(StrEnum):
    COHERENT = "coherent"
    COHERENT_WITH_RESIDUALS = "coherent_with_residuals"
    BLOCKED = "blocked"
    NOT_CHECKED = "not_checked"


SCHEMA_CHECKS: frozenset[str] = frozenset(
    {"SchemaOK", "DigestPolicyOK", "ObjectDigestOK", "BundleDigestOK"}
)
RECORD_CHECKS: frozenset[str] = frozenset({"RefGraphOK", "StatusOK", "ResidualOK"})
EVIDENCE_CHECKS: frozenset[str] = frozenset({"JudgmentOK"})
SUPPORT_CHECKS: frozenset[str] = frozenset({"RefGraphOK", "StatusOK", "ResidualOK", "JudgmentOK"})
AUTHORITY_CHECKS: frozenset[str] = frozenset({"AuthorityOK"})
ECOLOGY_CHECKS: frozenset[str] = frozenset({"EcologyOK"})


@dataclass(frozen=True)
class SemanticCheckReport:
    """Profile-aware summary of checkable operational semantics.

    The report states which executable levels were checked. It intentionally does not
    claim a theorem proof or a complete formal semantics for Verifier Ecology Theory.
    """

    profile: str
    required_levels: tuple[SemanticLevel, ...]
    checked_levels: tuple[SemanticLevel, ...]
    passed_levels: tuple[SemanticLevel, ...]
    residualized_levels: tuple[SemanticLevel, ...]
    failed_levels: tuple[SemanticLevel, ...]
    schema_valid: bool
    record_valid: bool
    evidence_valid: SupportEligibility
    support_valid: SupportEligibility
    authority_valid: AuthorityEligibility
    ecology_valid: EcologyEligibility
    residual_obligations: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()
    boundary_note: str = (
        "Executable VET-style operational checks only; this is not a theorem proof "
        "or complete formal semantics of Verifier Ecology Theory."
    )
    complete_formal_semantics_claim: bool = False

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)

    @property
    def required_levels_passed(self) -> bool:
        blocked = set(self.failed_levels)
        missing = set(self.required_levels) - set(self.checked_levels)
        return not blocked.intersection(self.required_levels) and not missing

    @classmethod
    def from_results(
        cls,
        *,
        profile: ConformanceProfile,
        ordered_check_results: list[CheckResult],
    ) -> SemanticCheckReport:
        by_name = {result.check_name: result for result in ordered_check_results}
        checked_levels: list[SemanticLevel] = []
        passed_levels: list[SemanticLevel] = []
        residualized_levels: list[SemanticLevel] = []
        failed_levels: list[SemanticLevel] = []
        residuals: list[str] = []
        failures: list[str] = []

        level_map = (
            (SemanticLevel.SCHEMA, SCHEMA_CHECKS),
            (SemanticLevel.RECORD, RECORD_CHECKS),
            (SemanticLevel.EVIDENCE, EVIDENCE_CHECKS),
            (SemanticLevel.SUPPORT, SUPPORT_CHECKS),
            (SemanticLevel.AUTHORITY, AUTHORITY_CHECKS),
            (SemanticLevel.ECOLOGY, ECOLOGY_CHECKS),
        )
        for level, names in level_map:
            results = [by_name[name] for name in names if name in by_name]
            if not results:
                continue
            checked_levels.append(level)
            residuals.extend(ref for result in results for ref in result.residual_refs)
            failures.extend(code.value for result in results for code in result.failure_codes)
            if any(result.result == CheckOutcome.FAIL for result in results):
                failed_levels.append(level)
            elif any(result.result == CheckOutcome.RESIDUALIZE for result in results):
                residualized_levels.append(level)
            elif all(result.passed for result in results):
                passed_levels.append(level)

        return cls(
            profile=profile.value,
            required_levels=required_levels_for_profile(profile),
            checked_levels=tuple(checked_levels),
            passed_levels=tuple(passed_levels),
            residualized_levels=tuple(residualized_levels),
            failed_levels=tuple(failed_levels),
            schema_valid=_level_passed(SemanticLevel.SCHEMA, passed_levels),
            record_valid=_level_not_failed(
                SemanticLevel.RECORD,
                checked_levels=checked_levels,
                failed_levels=failed_levels,
            ),
            evidence_valid=_support_eligibility(
                SemanticLevel.EVIDENCE,
                checked_levels,
                passed_levels,
                residualized_levels,
                failed_levels,
            ),
            support_valid=_support_eligibility(
                SemanticLevel.SUPPORT,
                checked_levels,
                passed_levels,
                residualized_levels,
                failed_levels,
            ),
            authority_valid=_authority_eligibility(
                checked_levels, passed_levels, residualized_levels, failed_levels
            ),
            ecology_valid=_ecology_eligibility(
                checked_levels, passed_levels, residualized_levels, failed_levels
            ),
            residual_obligations=tuple(dict.fromkeys(residuals)),
            failure_codes=tuple(dict.fromkeys(failures)),
        )


def required_levels_for_profile(profile: ConformanceProfile) -> tuple[SemanticLevel, ...]:
    if profile == ConformanceProfile.CORE:
        return (SemanticLevel.SCHEMA, SemanticLevel.RECORD)
    if profile == ConformanceProfile.OPERATIONAL:
        return (
            SemanticLevel.SCHEMA,
            SemanticLevel.RECORD,
            SemanticLevel.EVIDENCE,
            SemanticLevel.SUPPORT,
        )
    return tuple(SemanticLevel)


def _level_passed(level: SemanticLevel, passed_levels: list[SemanticLevel]) -> bool:
    return level in passed_levels


def _level_not_failed(
    level: SemanticLevel,
    *,
    checked_levels: list[SemanticLevel],
    failed_levels: list[SemanticLevel],
) -> bool:
    return level in checked_levels and level not in failed_levels


def _support_eligibility(
    level: SemanticLevel,
    checked_levels: list[SemanticLevel],
    passed_levels: list[SemanticLevel],
    residualized_levels: list[SemanticLevel],
    failed_levels: list[SemanticLevel],
) -> SupportEligibility:
    if level not in checked_levels:
        return SupportEligibility.NOT_CHECKED
    if level in failed_levels:
        return SupportEligibility.BLOCKED
    if level in residualized_levels:
        return SupportEligibility.ELIGIBLE_WITH_RESIDUALS
    if level in passed_levels:
        return SupportEligibility.ELIGIBLE
    return SupportEligibility.BLOCKED


def _authority_eligibility(
    checked_levels: list[SemanticLevel],
    passed_levels: list[SemanticLevel],
    residualized_levels: list[SemanticLevel],
    failed_levels: list[SemanticLevel],
) -> AuthorityEligibility:
    level = SemanticLevel.AUTHORITY
    if level not in checked_levels:
        return AuthorityEligibility.NOT_CHECKED
    if level in failed_levels:
        return AuthorityEligibility.BLOCKED
    if level in residualized_levels:
        return AuthorityEligibility.ALLOWABLE_WITH_RESIDUALS
    if level in passed_levels:
        return AuthorityEligibility.ALLOWABLE
    return AuthorityEligibility.BLOCKED


def _ecology_eligibility(
    checked_levels: list[SemanticLevel],
    passed_levels: list[SemanticLevel],
    residualized_levels: list[SemanticLevel],
    failed_levels: list[SemanticLevel],
) -> EcologyEligibility:
    level = SemanticLevel.ECOLOGY
    if level not in checked_levels:
        return EcologyEligibility.NOT_CHECKED
    if level in failed_levels:
        return EcologyEligibility.BLOCKED
    if level in residualized_levels:
        return EcologyEligibility.COHERENT_WITH_RESIDUALS
    if level in passed_levels:
        return EcologyEligibility.COHERENT
    return EcologyEligibility.BLOCKED
