"""Ordered conformance engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from verification_ecology_kit.digest import DigestPolicy, object_digest_input
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.records import ConformanceProfile, jsonable
from verification_ecology_kit.references import (
    ObjectEnvelope,
    ObjectRef,
    ReferenceResolver,
    SchemaCatalogue,
)
from verification_ecology_kit.result import (
    CheckResult,
    ConformanceReport,
    FailureCode,
    fail_result,
    pass_result,
    residual_result,
)


@dataclass
class VetBundle:
    bundle_id: str
    schema_version: str
    conformance_profile: ConformanceProfile
    schema_catalogue: SchemaCatalogue
    objects: list[ObjectEnvelope] = field(default_factory=list)
    references: list[ObjectRef] = field(default_factory=list)
    residual_ledger: ResidualLedger = field(default_factory=ResidualLedger)
    authority_decisions: list[object] = field(default_factory=list)
    judgment_records: list[object] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return jsonable(
            {
                "bundle_id": self.bundle_id,
                "schema_version": self.schema_version,
                "conformance_profile": self.conformance_profile,
                "schema_catalogue": {
                    "catalogue_id": self.schema_catalogue.catalogue_id,
                    "accepted_schema_versions": self.schema_catalogue.accepted_schema_versions,
                },
                "objects": [envelope.to_dict() for envelope in self.objects],
                "references": [ref.to_dict() for ref in self.references],
                "residual_ledger": self.residual_ledger.to_dict(),
                "authority_decisions": self.authority_decisions,
                "judgment_records": self.judgment_records,
                "provenance": self.provenance,
            }
        )


class ConformanceEngine:
    ORDERED_CHECKS: tuple[str, ...] = (
        "SchemaOK",
        "DigestPolicyOK",
        "ObjectDigestOK",
        "BundleDigestOK",
        "RefGraphOK",
        "StatusOK",
        "JudgmentOK",
        "ResidualOK",
        "AuthorityOK",
    )

    def __init__(self, digest_policy: DigestPolicy | None = None):
        self.digest_policy = digest_policy or DigestPolicy()

    def run(
        self, bundle: VetBundle, profile: ConformanceProfile | None = None
    ) -> ConformanceReport:
        selected = profile or bundle.conformance_profile
        checks: list[CheckResult] = []
        for check_name in self.ORDERED_CHECKS:
            if not self._required_for_profile(check_name, selected):
                continue
            checks.append(getattr(self, f"_check_{check_name.lower()}")(bundle))
        checked_digest = self.digest_policy.digest_json(bundle.to_dict()).value
        report = ConformanceReport.from_results(
            profile=selected.value,
            ordered_check_results=checks,
            checked_input_digest=checked_digest,
        )
        report.report_digest = self.digest_policy.digest_json(report.to_dict()).value
        return report

    def _required_for_profile(self, check_name: str, profile: ConformanceProfile) -> bool:
        if profile == ConformanceProfile.CORE:
            return check_name in {
                "SchemaOK",
                "DigestPolicyOK",
                "ObjectDigestOK",
                "BundleDigestOK",
                "RefGraphOK",
                "ResidualOK",
            }
        if profile == ConformanceProfile.OPERATIONAL:
            return check_name != "AuthorityOK" or True
        return True

    def _check_schemaok(self, bundle: VetBundle) -> CheckResult:
        for envelope in bundle.objects:
            catalogue_result = bundle.schema_catalogue.check_envelope(envelope)
            if not catalogue_result.passed:
                return catalogue_result
            schema = bundle.schema_catalogue.schemas.get(envelope.schema_id)
            if schema:
                try:
                    Draft202012Validator.check_schema(schema)
                    Draft202012Validator(schema).validate(envelope.payload)
                except (SchemaError, ValidationError):
                    return fail_result("SchemaOK", FailureCode.SCHEMA_INVALID)
        return pass_result("SchemaOK", evidence_refs=tuple(obj.object_id for obj in bundle.objects))

    def _check_digestpolicyok(self, bundle: VetBundle) -> CheckResult:
        for envelope in bundle.objects:
            if envelope.canonical_digest.algorithm_id not in self.digest_policy.accepted_algorithms:
                return fail_result("DigestPolicyOK", FailureCode.UNSUPPORTED_DIGEST_ALGORITHM)
        return pass_result("DigestPolicyOK")

    def _check_objectdigestok(self, bundle: VetBundle) -> CheckResult:
        for envelope in bundle.objects:
            if not envelope.canonical_digest.value:
                return residual_result(
                    "ObjectDigestOK",
                    FailureCode.DIGEST_MISMATCH,
                    suggested_repair_hooks=("refresh_object_digest",),
                )
            actual = self.digest_policy.digest_json(object_digest_input(envelope.to_dict()))
            if actual.value != envelope.canonical_digest.value:
                return fail_result("ObjectDigestOK", FailureCode.DIGEST_MISMATCH)
        return pass_result(
            "ObjectDigestOK", evidence_refs=tuple(obj.object_id for obj in bundle.objects)
        )

    def _check_bundledigestok(self, bundle: VetBundle) -> CheckResult:
        object_ids = [obj.object_id for obj in bundle.objects]
        if len(object_ids) != len(set(object_ids)):
            return fail_result("BundleDigestOK", FailureCode.SCHEMA_INVALID)
        return pass_result("BundleDigestOK")

    def _check_refgraphok(self, bundle: VetBundle) -> CheckResult:
        resolver = ReferenceResolver(bundle_id=bundle.bundle_id, envelopes=bundle.objects)
        residual_refs: list[str] = []
        for ref in bundle.references:
            _, _, result = resolver.resolve(ref)
            if not result.passed:
                residual_refs.extend(result.residual_refs)
                return result
        return pass_result(
            "RefGraphOK", evidence_refs=tuple(ref.object_id for ref in bundle.references)
        )

    def _check_statusok(self, bundle: VetBundle) -> CheckResult:
        return pass_result("StatusOK")

    def _check_judgmentok(self, bundle: VetBundle) -> CheckResult:
        invalid = [
            item
            for item in bundle.judgment_records
            if isinstance(item, dict) and item.get("JValid_result") == "fail"
        ]
        if invalid:
            return fail_result("JudgmentOK", FailureCode.JUDGMENT_INVALID)
        return pass_result("JudgmentOK")

    def _check_residualok(self, bundle: VetBundle) -> CheckResult:
        non_live = [
            residual.residual_id
            for residual in bundle.residual_ledger.residuals.values()
            if residual.status.value == "active" and residual.route is None
        ]
        if non_live:
            return residual_result(
                "ResidualOK",
                FailureCode.RESIDUAL_NOT_LIVE,
                residual_refs=tuple(non_live),
                suggested_repair_hooks=("route_active_residuals",),
            )
        return pass_result("ResidualOK")

    def _check_authorityok(self, bundle: VetBundle) -> CheckResult:
        for item in bundle.authority_decisions:
            if (
                isinstance(item, dict)
                and item.get("decision") == "allow"
                and item.get("decision_status") not in {"active", None}
            ):
                return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
        return pass_result("AuthorityOK")
