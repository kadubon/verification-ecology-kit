"""Continuation specifications, reachability certificates, and counterexample channels."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.records import LifecycleStatus, ReachabilityMode, jsonable
from verification_ecology_kit.model.residuals import SoundGapResidual, check_residual_liveness
from verification_ecology_kit.result import (
    CheckResult,
    FailureCode,
    fail_result,
    pass_result,
    residual_result,
)


@dataclass
class ContinuationSpecification:
    cont_spec_id: str
    membership_carrier_id: str
    coverage_carrier_id: str
    mode: ReachabilityMode
    horizon: str
    resource_bounds: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    negative_evidence_channel_ref: str = ""
    residual_obligations: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()


@dataclass
class CounterexampleChannel:
    channel_id: str
    target_ref: str
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    last_checked: str = ""
    search_window: str = ""
    budget: tuple[str, ...] = ()
    freshness_interval: str = ""
    unresolved_reports: tuple[str, ...] = ()
    stale_condition: str = ""
    adversarial_ingress: tuple[str, ...] = ()
    cex_closed_result: str = "not_checked"
    residual_obligations: tuple[str, ...] = ()

    def cex_closed(self) -> CheckResult:
        if self.status != LifecycleStatus.ACTIVE:
            return fail_result("CexClosed", FailureCode.STATUS_BLOCKS_SUPPORT)
        if self.unresolved_reports:
            return fail_result("CexClosed", FailureCode.EXPIRED_COUNTEREXAMPLE_CLOSURE)
        if self.cex_closed_result == "closed_within_window":
            return pass_result("CexClosed", evidence_refs=(self.channel_id,))
        return residual_result(
            "CexClosed",
            FailureCode.EXPIRED_COUNTEREXAMPLE_CLOSURE,
            residual_refs=self.residual_obligations,
        )


@dataclass
class ReachabilityCertificate:
    certificate_id: str
    object_id: str
    schema_version: str
    canonical_digest: Digest
    status: LifecycleStatus
    predicate: str
    certificate_contract: str
    carrier_id: str
    carrier_acceptance_judgment_ref: str
    carrier_type: str
    concretization_id: str
    checker_id: str
    checker_acceptance_judgment_ref: str
    checker_result: str
    claim_kind: str
    coverage_statement: str
    cover_check_result: str
    empty_concretization_statement: str
    empty_check_result: str
    cex_channel: CounterexampleChannel
    soundness_target: str
    operational_claim_basis: tuple[str, ...] = ()
    soundgap_residuals: tuple[SoundGapResidual, ...] = ()
    assumptions: tuple[str, ...] = ()
    scope: tuple[str, ...] = ()
    horizon: str = ""
    resource_bounds: tuple[str, ...] = ()
    cost_bounds: tuple[str, ...] = ()
    latency_bounds: tuple[str, ...] = ()
    invalidation_conditions: tuple[str, ...] = ()
    recheck_trigger: str = ""
    migration_witness_ref: str = ""
    falsification_attempts: tuple[str, ...] = ()
    open_counterexample_residuals: tuple[str, ...] = ()
    residual_obligations: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def admissible_exclusion(self) -> CheckResult:
        if self.status != LifecycleStatus.ACTIVE:
            return fail_result("ReachabilityExclusion", FailureCode.STATUS_BLOCKS_SUPPORT)
        if self.claim_kind != "exclusion":
            return residual_result("ReachabilityExclusion", FailureCode.BOUNDARY_UNCHECKED)
        if self.cover_check_result != "pass" or self.empty_check_result != "pass":
            return fail_result("ReachabilityExclusion", FailureCode.BOUNDARY_UNCHECKED)
        cex = self.cex_channel.cex_closed()
        if not cex.passed:
            return cex
        for gap in self.soundgap_residuals:
            live = check_residual_liveness(gap)
            if not live.passed:
                return fail_result("ReachabilityExclusion", FailureCode.SOUNDGAP_NOT_LIVE)
        return pass_result("ReachabilityExclusion", evidence_refs=(self.certificate_id,))

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
