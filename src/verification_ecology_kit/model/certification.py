"""Certification records and promotion checks."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.records import LifecycleStatus, jsonable
from verification_ecology_kit.result import CheckResult, FailureCode, fail_result, pass_result

CERTIFICATION_PRESERVED_FIELDS: tuple[str, ...] = (
    "declared_scope",
    "declared_interval",
    "continuation_spec_ref",
    "packet_chain",
    "reachability_certificate_refs",
    "unsupported_assumptions",
    "residual_obligations",
    "evidence_refs",
    "update_triggers",
)


@dataclass
class ComponentContract:
    claim: str
    evidence_carrier: str
    stability_relation: str
    failure_threshold: str
    monitor: str
    negative_evidence_channel: str
    drift_detector: str
    residual_gate: str
    recheck_trigger: str
    support_result: str = "not_checked"


@dataclass
class CertificationProfile:
    observed_support: tuple[str, ...] = ()
    local_use_support: tuple[str, ...] = ()
    predictive_stability_support: tuple[str, ...] = ()
    transfer_stability_support: tuple[str, ...] = ()
    self_modification_support: tuple[str, ...] = ()
    frontier_effect: tuple[str, ...] = ()
    aperture_preservation: tuple[str, ...] = ()
    residual_monotonicity: tuple[str, ...] = ()
    component_contracts: tuple[ComponentContract, ...] = ()


@dataclass
class CertificationRecord:
    certification_record_id: str
    object_id: str
    schema_version: str
    canonical_digest: Digest
    lifecycle_status: LifecycleStatus
    stability_relation_id: str
    transition_policy_id: str
    declared_scope: tuple[str, ...]
    declared_interval: str
    continuation_spec_ref: str
    packet_chain: tuple[str, ...]
    certification_profile: CertificationProfile
    evidence_refs: tuple[str, ...] = ()
    monitor_refs: tuple[str, ...] = ()
    residual_gates: tuple[str, ...] = ()
    reachability_certificate_refs: tuple[str, ...] = ()
    unsupported_assumptions: tuple[str, ...] = ()
    residual_obligations: tuple[str, ...] = ()
    update_triggers: tuple[str, ...] = ()
    optional_dashboard_label: str = ""
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


class CertificationEngine:
    def promotion_check(
        self,
        earlier: CertificationRecord,
        later: CertificationRecord,
    ) -> CheckResult:
        missing: list[str] = []
        if not set(earlier.declared_scope).issubset(
            set(later.declared_scope) | set(later.residual_obligations)
        ):
            missing.append("declared_scope")
        for field_name in CERTIFICATION_PRESERVED_FIELDS[1:]:
            earlier_values = set(getattr(earlier, field_name))
            later_values = set(getattr(later, field_name)) | set(later.residual_obligations)
            if not earlier_values.issubset(later_values):
                missing.append(field_name)
        if missing:
            return fail_result(
                "CertificationPromotion",
                FailureCode.OVERCLOSURE_RISK,
                suggested_repair_hooks=tuple(f"preserve_or_residualize_{name}" for name in missing),
            )
        return pass_result("CertificationPromotion", evidence_refs=(later.certification_record_id,))
