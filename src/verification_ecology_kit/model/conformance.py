"""Ordered conformance engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from verification_ecology_kit.digest import DigestPolicy, object_digest_input
from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine
from verification_ecology_kit.model.judgments import jvalid
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.lifecycle import StatusEvent, StatusFold, StatusView
from verification_ecology_kit.model.records import (
    AuthorityDecisionValue,
    ConformanceProfile,
    LifecycleStatus,
    jsonable,
)
from verification_ecology_kit.model.residuals import check_residual_liveness
from verification_ecology_kit.model.semantics import SemanticCheckReport
from verification_ecology_kit.model.serde import (
    auth_inputs_from_json,
    judgment_contract_from_json,
    judgment_record_from_json,
    object_ref_from_json,
    use_context_from_json,
)
from verification_ecology_kit.references import (
    ObjectEnvelope,
    ObjectRef,
    ReferenceResolver,
    SchemaCatalogue,
    SupportReferenceResolver,
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
                    "schemas": self.schema_catalogue.schemas,
                    "migration_witnesses": {
                        f"{source}->{target}": witness
                        for (
                            source,
                            target,
                        ), witness in self.schema_catalogue.migration_witnesses.items()
                    },
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
        "EcologyOK",
    )

    def __init__(self, digest_policy: DigestPolicy | None = None):
        self.digest_policy = digest_policy or DigestPolicy()
        self._active_profile = ConformanceProfile.CORE

    def run(
        self, bundle: VetBundle, profile: ConformanceProfile | None = None
    ) -> ConformanceReport:
        selected = profile or bundle.conformance_profile
        self._active_profile = selected
        checks: list[CheckResult] = []
        if selected != ConformanceProfile.CORE and not bundle.objects:
            checks.append(
                fail_result(
                    "OperationalBundleNonEmpty",
                    FailureCode.SCHEMA_INVALID,
                    suggested_repair_hooks=("add_statused_objects_or_use_core_profile",),
                )
            )
        for check_name in self.ORDERED_CHECKS:
            if not self._required_for_profile(check_name, selected, bundle):
                continue
            checks.append(getattr(self, f"_check_{check_name.lower()}")(bundle))
        checked_digest = self.digest_policy.digest_json(bundle.to_dict()).value
        report = ConformanceReport.from_results(
            profile=selected.value,
            ordered_check_results=checks,
            checked_input_digest=checked_digest,
        )
        semantic_report = SemanticCheckReport.from_results(
            profile=selected,
            ordered_check_results=checks,
        )
        report.semantic_report = semantic_report.to_dict()
        report.report_digest = self.digest_policy.digest_json(report.to_dict()).value
        return report

    def _required_for_profile(
        self,
        check_name: str,
        profile: ConformanceProfile,
        bundle: VetBundle,
    ) -> bool:
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
            if check_name == "AuthorityOK":
                return bool(bundle.authority_decisions)
            return check_name != "EcologyOK"
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
        resolver = ReferenceResolver(bundle_id=bundle.bundle_id, envelopes=bundle.objects)
        evidence_refs: list[str] = []
        for envelope in bundle.objects:
            status: LifecycleStatus | None
            folded = self._status_fold_from_payload(envelope.object_id, envelope.payload)
            if folded is not None:
                status_view, result = folded
                if not result.passed:
                    return result
                status = status_view.status
                evidence_refs.extend(status_view.status_event_refs)
            else:
                status = self._status_from_payload(envelope.payload)
            if envelope.status_ref is not None:
                _, target, result = resolver.resolve(envelope.status_ref)
                if not result.passed:
                    return fail_result("StatusOK", FailureCode.UNRESOLVED_REFERENCE)
                if isinstance(target, dict):
                    folded = self._status_fold_from_payload(envelope.object_id, target)
                    if folded is not None:
                        status_view, fold_result = folded
                        if not fold_result.passed:
                            return fold_result
                        status = status_view.status
                        evidence_refs.extend(status_view.status_event_refs)
                    else:
                        status = self._status_from_payload(target)
                else:
                    status = self._status_from_payload(target)
                evidence_refs.append(envelope.status_ref.object_id)
            if status is None:
                return residual_result(
                    "StatusOK",
                    FailureCode.STATUS_BLOCKS_SUPPORT,
                    suggested_repair_hooks=("attach_status_ref_or_lifecycle_status",),
                )
            if status not in {LifecycleStatus.ACTIVE, LifecycleStatus.MIGRATED}:
                return fail_result("StatusOK", FailureCode.STATUS_BLOCKS_SUPPORT)
            evidence_refs.append(envelope.object_id)
        return pass_result("StatusOK", evidence_refs=tuple(dict.fromkeys(evidence_refs)))

    def _check_judgmentok(self, bundle: VetBundle) -> CheckResult:
        evidence_refs: list[str] = []
        support_resolver = SupportReferenceResolver(
            bundle_id=bundle.bundle_id,
            envelopes=bundle.objects,
            schema_catalogue=bundle.schema_catalogue,
        )
        for item in bundle.judgment_records:
            record = self._record_dict(item)
            if record is None:
                return fail_result("JudgmentOK", FailureCode.JUDGMENT_INVALID)
            status = self._status_from_payload(record)
            if status is not None and status not in {
                LifecycleStatus.ACTIVE,
                LifecycleStatus.MIGRATED,
            }:
                return fail_result("JudgmentOK", FailureCode.STATUS_BLOCKS_SUPPORT)
            expected_contract = record.get("expected_contract_version")
            if (
                expected_contract is not None
                and record.get("contract_version") != expected_contract
            ):
                return fail_result("JudgmentOK", FailureCode.JUDGMENT_INVALID)
            expected_input_digest = record.get("expected_input_digest")
            if (
                expected_input_digest is not None
                and record.get("input_digest") != expected_input_digest
            ):
                return fail_result("JudgmentOK", FailureCode.DIGEST_MISMATCH)
            allowed_results = record.get("allowed_results")
            if isinstance(allowed_results, list) and record.get("result") not in allowed_results:
                return fail_result("JudgmentOK", FailureCode.JUDGMENT_INVALID)
            reconstructed = self._run_reconstructed_jvalid(bundle, support_resolver, record)
            if reconstructed is not None:
                if not reconstructed.passed:
                    return fail_result("JudgmentOK", *reconstructed.failure_codes)
                judgment_id = record.get("judgment_id")
                if judgment_id is not None:
                    evidence_refs.append(str(judgment_id))
                continue
            jvalid = str(
                record.get("jvalid_result", record.get("JValid_result", "not_checked"))
            ).lower()
            if jvalid == "fail":
                return fail_result("JudgmentOK", FailureCode.JUDGMENT_INVALID)
            if jvalid == "pass":
                return fail_result(
                    "JudgmentOK",
                    FailureCode.JUDGMENT_INVALID,
                    suggested_repair_hooks=("provide_judgment_record_use_context_and_contract",),
                )
            if jvalid == "not_applicable":
                if record.get("authority_use") or record.get("operational_use"):
                    return fail_result("JudgmentOK", FailureCode.JUDGMENT_INVALID)
            elif jvalid not in {"not_applicable"}:
                return residual_result(
                    "JudgmentOK",
                    FailureCode.JUDGMENT_INVALID,
                    suggested_repair_hooks=("run_jvalid_or_mark_not_applicable",),
                )
            judgment_id = record.get("judgment_id")
            if judgment_id is not None:
                evidence_refs.append(str(judgment_id))
        return pass_result("JudgmentOK", evidence_refs=tuple(evidence_refs))

    def _check_residualok(self, bundle: VetBundle) -> CheckResult:
        non_live: list[str] = []
        for residual in bundle.residual_ledger.residuals.values():
            result = check_residual_liveness(residual)
            if not result.passed:
                non_live.append(residual.residual_id)
        if non_live:
            return residual_result(
                "ResidualOK",
                FailureCode.RESIDUAL_NOT_LIVE,
                residual_refs=tuple(non_live),
                suggested_repair_hooks=("route_active_residuals",),
            )
        return pass_result("ResidualOK")

    def _check_authorityok(self, bundle: VetBundle) -> CheckResult:
        if self._active_profile == ConformanceProfile.FEDERATED and not bundle.authority_decisions:
            return fail_result(
                "AuthorityOK",
                FailureCode.AUTHORITY_MISMATCH,
                suggested_repair_hooks=("attach_active_authority_decision",),
            )
        support_resolver = SupportReferenceResolver(
            bundle_id=bundle.bundle_id,
            envelopes=bundle.objects,
            schema_catalogue=bundle.schema_catalogue,
        )
        for item in bundle.authority_decisions:
            record = self._record_dict(item)
            if record is None:
                return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
            decision = str(record.get("decision", "deny")).lower()
            if not bool(record.get("deny_by_default", True)):
                return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
            status = self._status_from_payload(record)
            if status is not None and status not in {
                LifecycleStatus.ACTIVE,
                LifecycleStatus.MIGRATED,
            }:
                return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
            if decision == "allow":
                required_support_items = list(record.get("required_support_refs", ()))
                auth_inputs_data = self._auth_inputs_payload(bundle, record)
                if auth_inputs_data is not None:
                    try:
                        auth_inputs = auth_inputs_from_json(
                            auth_inputs_data,
                            bundle_id=bundle.bundle_id,
                        )
                    except ValueError:
                        return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
                    required_support_items.extend(auth_inputs.support_refs)
                    candidate_ref = self._support_ref_from_any(bundle, auth_inputs.candidate_ref)
                    candidate_resolution = support_resolver.resolve_authority_ref(
                        candidate_ref,
                        require_object=True,
                    )
                    if not candidate_resolution.check_result.passed:
                        return fail_result(
                            "AuthorityOK",
                            FailureCode.AUTHORITY_MISMATCH,
                            residual_refs=(candidate_ref.object_id,),
                        )
                    if (
                        candidate_resolution.envelope is not None
                        and auth_inputs.canonical_digest.value
                        and candidate_resolution.envelope.canonical_digest.value
                        != auth_inputs.canonical_digest.value
                    ):
                        return fail_result(
                            "AuthorityOK",
                            FailureCode.DIGEST_MISMATCH,
                            residual_refs=(candidate_ref.object_id,),
                        )
                    if auth_inputs.counterexample_refs:
                        return fail_result(
                            "AuthorityOK",
                            FailureCode.AUTHORITY_MISMATCH,
                            residual_refs=auth_inputs.counterexample_refs,
                        )
                    if auth_inputs.policy_conflict_refs:
                        return fail_result(
                            "AuthorityOK",
                            FailureCode.AUTHORITY_MISMATCH,
                            residual_refs=auth_inputs.policy_conflict_refs,
                        )
                    missing_auxiliary = tuple(
                        ref
                        for ref in (
                            *auth_inputs.absence_cert_refs,
                            *auth_inputs.status_view_refs,
                        )
                        if self._payload_by_id(bundle, ref) is None
                    )
                    if missing_auxiliary:
                        return fail_result(
                            "AuthorityOK",
                            FailureCode.UNRESOLVED_REFERENCE,
                            residual_refs=missing_auxiliary,
                        )
                    if auth_inputs.soundgap_refs:
                        return fail_result(
                            "AuthorityOK",
                            FailureCode.SOUNDGAP_NOT_LIVE,
                            residual_refs=auth_inputs.soundgap_refs,
                        )
                elif required_support_items:
                    return fail_result(
                        "AuthorityOK",
                        FailureCode.AUTHORITY_MISMATCH,
                        suggested_repair_hooks=("attach_auth_inputs_ref",),
                    )
                required_support = tuple(str(ref) for ref in required_support_items)
                support_judgments = tuple(record.get("support_judgment_refs", ()))
                if required_support and not support_judgments:
                    return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
                support_blockers: list[str] = []
                for value in required_support_items:
                    ref = self._support_ref_from_any(bundle, value)
                    resolution = support_resolver.resolve_support(ref, require_object=True)
                    if not resolution.check_result.passed:
                        support_blockers.append(ref.object_id)
                if support_blockers:
                    return fail_result(
                        "AuthorityOK",
                        FailureCode.AUTHORITY_MISMATCH,
                        residual_refs=tuple(dict.fromkeys(support_blockers)),
                    )
                denial_refs = self._authority_denial_refs(record)
                if denial_refs:
                    return fail_result(
                        "AuthorityOK",
                        FailureCode.AUTHORITY_MISMATCH,
                        residual_refs=denial_refs,
                    )
                decision_record = self._authority_decision_from_record(record)
                if decision_record is not None:
                    decision_record.required_support_refs = required_support
                    decision_record.support_judgment_refs = support_judgments
                    decision_record.residual_gates = tuple(
                        str(ref) for ref in record.get("residual_gates", ())
                    )
                    decision_record.rollback_hooks_required = tuple(
                        str(ref) for ref in record.get("rollback_hooks_required", ())
                    )
                    decision_record.required_human_assessment_roles = tuple(
                        str(ref) for ref in record.get("required_human_assessment_roles", ())
                    )
                    decision_record.required_tool_assessment_roles = tuple(
                        str(ref) for ref in record.get("required_tool_assessment_roles", ())
                    )
                _, aggregate = AuthorityEngine().aggregate(
                    self._authority_action(record),
                    [decision_record] if decision_record else [],
                    required_support_refs=required_support,
                )
                if not aggregate.passed:
                    return aggregate
                continue
            if decision == "residualize":
                residual_refs = tuple(str(ref) for ref in record.get("residual_gates", ()))
                return residual_result(
                    "AuthorityOK",
                    FailureCode.AUTHORITY_MISMATCH,
                    residual_refs=residual_refs,
                    suggested_repair_hooks=("clear_authority_residual_gates",),
                )
            return fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH)
        if bundle.authority_decisions:
            refs = [
                str(record.get("authority_decision_id"))
                for item in bundle.authority_decisions
                if (record := self._record_dict(item)) and record.get("authority_decision_id")
            ]
            return pass_result("AuthorityOK", evidence_refs=tuple(refs))
        return pass_result("AuthorityOK")

    def _check_ecologyok(self, bundle: VetBundle) -> CheckResult:
        trace = bundle.residual_ledger.trace_ok()
        if not trace.passed:
            return fail_result("EcologyOK", *trace.failure_codes)
        authority_blocking: list[str] = []
        for residual in bundle.residual_ledger.residuals.values():
            if (
                residual.status.value == "active"
                and residual.route is not None
                and residual.route.authority_effect == "blocks_authority"
                and not check_residual_liveness(residual).passed
            ):
                authority_blocking.append(residual.residual_id)
        if authority_blocking:
            return residual_result(
                "EcologyOK",
                FailureCode.RESIDUAL_NOT_LIVE,
                residual_refs=tuple(authority_blocking),
                suggested_repair_hooks=("repair_authority_blocking_residual_routes",),
            )
        return pass_result("EcologyOK")

    def _run_reconstructed_jvalid(
        self,
        bundle: VetBundle,
        support_resolver: SupportReferenceResolver,
        record: dict[str, Any],
    ) -> CheckResult | None:
        context_data = record.get("use_context")
        if context_data is None and record.get("use_context_ref"):
            context_data = self._payload_by_id(bundle, str(record["use_context_ref"]))
        contract_data = record.get("contract")
        if contract_data is None:
            ref = record.get("contract_ref") or record.get("checker_or_policy_ref")
            if ref:
                contract_data = self._payload_by_id(bundle, str(ref))
        if context_data is None or contract_data is None:
            return None
        try:
            judgment = judgment_record_from_json(record, bundle_id=bundle.bundle_id)
            context = use_context_from_json(context_data, bundle_id=bundle.bundle_id)
            contract = judgment_contract_from_json(contract_data)
        except (KeyError, ValueError):
            return fail_result("JValid", FailureCode.JUDGMENT_INVALID)
        subject_resolution = support_resolver.resolve_support(context.subject_ref)
        if not subject_resolution.check_result.passed:
            return fail_result("JValid", *subject_resolution.check_result.failure_codes)
        input_resolution = support_resolver.resolve_support(context.resolved_input_ref)
        if not input_resolution.check_result.passed:
            return fail_result("JValid", *input_resolution.check_result.failure_codes)
        if (
            input_resolution.envelope is not None
            and context.input_digest.value
            and input_resolution.envelope.canonical_digest.value != context.input_digest.value
        ):
            return fail_result("JValid", FailureCode.DIGEST_MISMATCH)
        return jvalid(judgment, context, contract)

    def _payload_by_id(self, bundle: VetBundle, object_id: str) -> dict[str, Any] | None:
        for envelope in bundle.objects:
            if envelope.object_id == object_id:
                return envelope.payload
        return None

    def _auth_inputs_payload(
        self, bundle: VetBundle, record: dict[str, Any]
    ) -> dict[str, Any] | None:
        embedded = record.get("auth_inputs")
        if isinstance(embedded, dict):
            return embedded
        ref = record.get("auth_inputs_ref")
        if isinstance(ref, str) and ref:
            return self._payload_by_id(bundle, ref)
        return None

    def _support_ref_from_any(self, bundle: VetBundle, value: object) -> ObjectRef:
        if isinstance(value, dict):
            return object_ref_from_json(value, bundle_id=bundle.bundle_id)
        object_id = str(value)
        for envelope in bundle.objects:
            if envelope.object_id == object_id:
                return ObjectRef(
                    bundle_id=bundle.bundle_id,
                    object_id=object_id,
                    schema_id=envelope.schema_id,
                    digest=envelope.canonical_digest,
                )
        return ObjectRef(bundle_id=bundle.bundle_id, object_id=object_id, schema_id="")

    def _authority_decision_from_record(self, record: dict[str, Any]) -> AuthorityDecision | None:
        from verification_ecology_kit.digest import Digest
        from verification_ecology_kit.model.records import AuthorityAction

        try:
            return AuthorityDecision(
                authority_decision_id=str(record.get("authority_decision_id", "")),
                object_id=str(record.get("object_id", "")),
                schema_version=str(record.get("schema_version", "")),
                canonical_digest=Digest("sha256", str(record.get("canonical_digest", ""))),
                lifecycle_status=self._status_from_payload(record) or LifecycleStatus.ACTIVE,
                policy_id=str(record.get("policy_id", "")),
                action=AuthorityAction(str(record.get("action", AuthorityAction.LOCAL_USE.value))),
                decision=AuthorityDecisionValue(str(record.get("decision", "deny"))),
                deny_by_default=bool(record.get("deny_by_default", True)),
                auth_inputs_ref=str(record.get("auth_inputs_ref", "")),
                required_support_refs=tuple(
                    str(item) for item in record.get("required_support_refs", ())
                ),
                support_judgment_refs=tuple(
                    str(item) for item in record.get("support_judgment_refs", ())
                ),
                sandbox_required=bool(record.get("sandbox_required", False)),
                sandbox_status=str(record.get("sandbox_status", "not_applicable")),
            )
        except ValueError:
            return None

    def _authority_denial_refs(self, record: dict[str, Any]) -> tuple[str, ...]:
        refs: list[str] = []
        support_statuses = record.get("support_statuses", {})
        if isinstance(support_statuses, dict):
            refs.extend(
                str(ref)
                for ref, status in support_statuses.items()
                if str(status) in {"stale", "unknown", "revoked"}
            )
        for key in (
            "migrated_without_witness_refs",
            "digest_mismatched_support_refs",
            "unresolved_support_refs",
            "counterexample_challenged_refs",
            "expired_cex_closed_refs",
            "non_live_soundgap_refs",
            "residual_gates",
        ):
            value = record.get(key, ())
            if isinstance(value, list | tuple):
                refs.extend(str(ref) for ref in value)
        if record.get("scope_action_match") == "fail":
            refs.append("scope_action_mismatch")
        if record.get("sandbox_required") and record.get("sandbox_status") != "active":
            refs.append("sandbox_inactive")
        if record.get("expiry_state") == "expired" or record.get("expired"):
            refs.append("authority_expired")
        return tuple(dict.fromkeys(refs))

    def _authority_action(self, record: dict[str, Any]) -> Any:
        from verification_ecology_kit.model.records import AuthorityAction

        try:
            return AuthorityAction(str(record.get("action", AuthorityAction.LOCAL_USE.value)))
        except ValueError:
            return AuthorityAction.LOCAL_USE

    def _status_from_payload(self, value: object) -> LifecycleStatus | None:
        if not isinstance(value, dict):
            return None
        for key in ("lifecycle_status", "status", "decision_status", "post_status"):
            if key in value:
                try:
                    return LifecycleStatus(str(value[key]))
                except ValueError:
                    return LifecycleStatus.UNKNOWN
        payload = value.get("payload")
        if isinstance(payload, dict):
            return self._status_from_payload(payload)
        return None

    def _record_dict(self, item: object) -> dict[str, Any] | None:
        if isinstance(item, dict):
            return item
        to_dict = getattr(item, "to_dict", None)
        if callable(to_dict):
            record = to_dict()
            if isinstance(record, dict):
                return record
        return None

    def _status_fold_from_payload(
        self, object_id: str, value: object
    ) -> tuple[StatusView, CheckResult] | None:
        if not isinstance(value, dict):
            return None
        raw_events = value.get("status_events")
        if not isinstance(raw_events, list):
            return None
        events: list[StatusEvent] = []
        for raw in raw_events:
            if not isinstance(raw, dict):
                return None
            try:
                events.append(
                    StatusEvent(
                        object_id=str(raw.get("object_id", object_id)),
                        pre_status=LifecycleStatus(str(raw.get("pre_status", "unknown"))),
                        post_status=LifecycleStatus(str(raw.get("post_status", "unknown"))),
                        cause=str(raw.get("cause", "status fold")),
                        actor_authority_ref=str(raw.get("actor_authority_ref", "local")),
                        ledger_event_ref=str(raw.get("ledger_event_ref", "")),
                        invalidation_trigger=str(raw.get("invalidation_trigger", "")),
                        migration_target=str(raw.get("migration_target", "")),
                        residual_disposition=tuple(
                            str(item) for item in raw.get("residual_disposition", ())
                        ),
                        predecessor_event_ref=raw.get("predecessor_event_ref"),
                        provenance=tuple(str(item) for item in raw.get("provenance", ())),
                        status_event_id=str(raw.get("status_event_id") or raw.get("id") or ""),
                    )
                )
            except ValueError:
                status_view, result = StatusFold().fold(object_id, [])
                return status_view, result
        return StatusFold().fold(object_id, events)
