"""Stable JSON-to-model loaders for VET records."""

from __future__ import annotations

from typing import Any

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.authority import AuthInputs
from verification_ecology_kit.model.contracts import JudgmentContract
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.history import HistoryEvent, ObservableProcessHistory
from verification_ecology_kit.model.judgments import JudgmentRecord, UseContext
from verification_ecology_kit.model.ledger import LedgerEvent, ResidualLedger
from verification_ecology_kit.model.packets import (
    AntiOverclosure,
    BoundaryRefs,
    CertificationCondition,
    CirculationStatus,
    EcologicalInvariants,
    PacketOrigin,
    PacketScope,
    ResidualHooks,
    ResidualLivenessPolicy,
    TransformationClass,
    UpdateProfile,
    VerifierPacket,
    VerifierProcedure,
)
from verification_ecology_kit.model.reachability import (
    CounterexampleChannel,
    ReachabilityCertificate,
)
from verification_ecology_kit.model.records import (
    AuthorityAction,
    LedgerStatus,
    LifecycleStatus,
    OriginKind,
    ResidualKind,
    ResidualMetabolismRoute,
    TrustStatus,
    Visibility,
)
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute, SoundGapResidual
from verification_ecology_kit.references import ObjectRef


def as_dict(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def optional_dict(value: Any, *, name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return as_dict(value, name=name)


def dict_value(value: Any, *, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    return as_dict(value, name=name)


def string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list | tuple):
        raise ValueError("expected a list of strings")
    return [str(item) for item in value]


def string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(string_list(value))


def digest_from_json(value: Any, *, default_algorithm: str = "sha256") -> Digest:
    if isinstance(value, Digest):
        return value
    if isinstance(value, str):
        return Digest(default_algorithm, value)
    data = as_dict(value or {}, name="digest")
    return Digest(
        algorithm_id=str(data.get("algorithm_id", default_algorithm)),
        value=str(data.get("value", "")),
    )


def object_ref_from_json(value: Any, *, bundle_id: str = "") -> ObjectRef:
    if isinstance(value, ObjectRef):
        return value
    if isinstance(value, str):
        return ObjectRef(bundle_id=bundle_id, object_id=value, schema_id="")
    data = as_dict(value, name="object reference")
    digest_value = data.get("digest")
    return ObjectRef(
        bundle_id=str(data.get("bundle_id", bundle_id)),
        object_id=str(data.get("object_id", "")),
        schema_id=str(data.get("schema_id", "")),
        pointer=str(data.get("pointer", "")),
        digest_algorithm_id=str(data.get("digest_algorithm_id", "sha256")),
        digest=digest_from_json(digest_value) if digest_value is not None else None,
        intended_use=str(data.get("intended_use", "support")),
    )


def judgment_contract_from_json(value: Any) -> JudgmentContract:
    data = as_dict(value, name="judgment contract")
    return JudgmentContract(
        judgment_kind=str(data.get("judgment_kind", "")),
        subject_type=str(data.get("subject_type", "")),
        input_digest_type=str(data.get("input_digest_type", "object_digest")),
        checker_or_policy_type=str(data.get("checker_or_policy_type", "")),
        result_type=str(data.get("result_type", "check_result")),
        allowed_results=string_tuple(data.get("allowed_results", ("pass", "fail", "residualize"))),
        freshness_interval=str(data.get("freshness_interval", "")),
        invalidation_triggers=string_tuple(data.get("invalidation_triggers")),
        recheck_trigger=str(data.get("recheck_trigger", "")),
        residual_schema_ref=str(data.get("residual_schema_ref", "")),
        version=str(data.get("version", data.get("contract_version", "1"))),
    )


def use_context_from_json(value: Any, *, bundle_id: str = "") -> UseContext:
    data = as_dict(value, name="use context")
    subject_ref = object_ref_from_json(
        data.get("subject_ref", data.get("subject")),
        bundle_id=bundle_id,
    )
    input_ref = object_ref_from_json(
        data.get("resolved_input_ref", data.get("canonical_input_ref", subject_ref.to_dict())),
        bundle_id=bundle_id,
    )
    canonical_input_ref = object_ref_from_json(
        data.get("canonical_input_ref", input_ref.to_dict()), bundle_id=bundle_id
    )
    return UseContext(
        subject_ref=subject_ref,
        subject_pointer=str(data.get("subject_pointer", data.get("input_pointer", ""))),
        resolved_input_ref=input_ref,
        scope=string_tuple(data.get("scope")),
        action=str(data.get("action", "local_use")),
        ledger_ref=str(data.get("ledger_ref", "")),
        policy_id=str(data.get("policy_id", "")),
        schema_version=str(data.get("schema_version", "")),
        digest_algorithm_id=str(data.get("digest_algorithm_id", "sha256")),
        canonical_input_ref=canonical_input_ref,
        input_digest=digest_from_json(data.get("input_digest")),
        freshness_horizon=str(data.get("freshness_horizon", "")),
        resource_bounds=string_tuple(data.get("resource_bounds")),
        clock_context=str(data.get("clock_context", "")),
    )


def judgment_record_from_json(value: Any, *, bundle_id: str = "") -> JudgmentRecord:
    if isinstance(value, JudgmentRecord):
        return value
    data = as_dict(value, name="judgment record")
    subject = object_ref_from_json(data.get("subject"), bundle_id=bundle_id)
    canonical_input_ref = object_ref_from_json(data.get("canonical_input_ref"), bundle_id=bundle_id)
    return JudgmentRecord(
        judgment_id=str(data.get("judgment_id") or new_id("jud")),
        judgment_kind=str(data.get("judgment_kind", "")),
        subject=subject,
        checker_or_policy_ref=str(data.get("checker_or_policy_ref", "")),
        contract_version=str(data.get("contract_version", "")),
        schema_version=str(data.get("schema_version", "")),
        object_id=str(data.get("object_id", subject.object_id)),
        canonical_digest=digest_from_json(data.get("canonical_digest")),
        use_context_ref=str(data.get("use_context_ref", "")),
        canonical_input_ref=canonical_input_ref,
        input_pointer=str(data.get("input_pointer", "")),
        input_digest=digest_from_json(data.get("input_digest")),
        digest_algorithm_id=str(data.get("digest_algorithm_id", "sha256")),
        result=str(data.get("result", "")),
        jvalid_result=str(data.get("jvalid_result", data.get("JValid_result", "not_checked"))),
        status=LifecycleStatus(str(data.get("status", LifecycleStatus.ACTIVE.value))),
        assumptions=string_tuple(data.get("assumptions")),
        evidence_refs=string_tuple(data.get("evidence_refs")),
        residuals=string_tuple(data.get("residuals")),
        provenance=string_tuple(data.get("provenance")),
        timestamp_or_clock=str(data.get("timestamp_or_clock", "")),
    )


def auth_inputs_from_json(value: Any, *, bundle_id: str = "") -> AuthInputs:
    data = as_dict(value, name="authority inputs")
    return AuthInputs(
        auth_inputs_ref=str(data.get("auth_inputs_ref", data.get("id", ""))),
        object_id=str(data.get("object_id", "")),
        schema_version=str(data.get("schema_version", "")),
        canonical_digest=digest_from_json(data.get("canonical_digest")),
        candidate_ref=str(data.get("candidate_ref", "")),
        action=AuthorityAction(str(data.get("action", AuthorityAction.LOCAL_USE.value))),
        action_scope=string_tuple(data.get("action_scope")),
        resolved_input_refs=string_tuple(data.get("resolved_input_refs")),
        support_refs=tuple(
            _object_ref_string(item, bundle_id=bundle_id) for item in data.get("support_refs", ())
        ),
        absence_cert_refs=string_tuple(data.get("absence_cert_refs")),
        counterexample_refs=string_tuple(data.get("counterexample_refs")),
        soundgap_refs=string_tuple(data.get("soundgap_refs")),
        status_view_refs=string_tuple(data.get("status_view_refs")),
        policy_conflict_refs=string_tuple(data.get("policy_conflict_refs")),
        input_digest=digest_from_json(data.get("input_digest"))
        if data.get("input_digest")
        else None,
    )


def _object_ref_string(value: Any, *, bundle_id: str) -> str:
    if isinstance(value, dict):
        return object_ref_from_json(value, bundle_id=bundle_id).object_id
    return str(value)


def packet_from_json(data: Any) -> VerifierPacket:
    data = as_dict(data, name="packet JSON")
    packet = VerifierPacket(
        origin=origin_from_json(optional_dict(data.get("origin"), name="origin")),
        scope=scope_from_json(optional_dict(data.get("scope"), name="scope")),
        transformation_class=transformation_from_json(
            optional_dict(data.get("transformation_class"), name="transformation_class")
        ),
        verifier_procedure=procedure_from_json(
            optional_dict(data.get("verifier_procedure"), name="verifier_procedure")
        ),
        certification_condition=certification_condition_from_json(
            optional_dict(data.get("certification_condition"), name="certification_condition")
        ),
        boundary_refs=boundary_refs_from_json(
            optional_dict(data.get("boundary_refs"), name="boundary_refs")
        ),
        residual_hooks=residual_hooks_from_json(
            optional_dict(data.get("residual_hooks"), name="residual_hooks")
        ),
        update_profile=update_profile_from_json(
            optional_dict(data.get("update_profile"), name="update_profile")
        ),
        circulation_status=circulation_status_from_json(
            optional_dict(data.get("circulation_status"), name="circulation_status")
        ),
        packet_id=str(data.get("packet_id") or new_id("pkt")),
        question_form=dict_value(data.get("question_form"), name="question_form"),
        extension=dict_value(data.get("extension"), name="extension"),
        residual_obligations=[
            residual_from_json(item) for item in data.get("residual_obligations", [])
        ],
        counter_packet_refs=string_list(data.get("counter_packet_refs")),
        anti_overclosure=anti_overclosure_from_json(
            optional_dict(data.get("anti_overclosure"), name="anti_overclosure")
        ),
        ecological_invariants=ecological_invariants_from_json(
            optional_dict(data.get("ecological_invariants"), name="ecological_invariants")
        ),
        residual_liveness=residual_liveness_from_json(
            optional_dict(data.get("residual_liveness"), name="residual_liveness")
        ),
    )
    packet.ensure_core_accountability()
    return packet


def origin_from_json(data: dict[str, Any] | None) -> PacketOrigin | None:
    if data is None:
        return None
    return PacketOrigin(
        created_from=OriginKind(str(data.get("created_from", OriginKind.HUMAN_SPECIFICATION))),
        traces=string_list(data.get("traces")),
        lineage=string_list(data.get("lineage")),
        parent_packets=string_list(data.get("parent_packets")),
        inherited_residuals=string_list(data.get("inherited_residuals")),
        inherited_boundaries=string_list(data.get("inherited_boundaries")),
        inherited_overclosure_exposures=string_list(data.get("inherited_overclosure_exposures")),
        unresolved_origin_residuals=string_list(data.get("unresolved_origin_residuals")),
    )


def scope_from_json(data: dict[str, Any] | None) -> PacketScope | None:
    if data is None:
        return None
    return PacketScope(
        applies_to=string_list(data.get("applies_to")),
        excludes=string_list(data.get("excludes")),
        assumptions=string_list(data.get("assumptions")),
        unvalidated_assumptions=string_list(data.get("unvalidated_assumptions")),
        known_misuse_contexts=string_list(data.get("known_misuse_contexts")),
        known_invalid_scopes=string_list(data.get("known_invalid_scopes")),
    )


def transformation_from_json(data: dict[str, Any] | None) -> TransformationClass | None:
    if data is None:
        return None
    return TransformationClass(
        allowed=string_list(data.get("allowed")),
        forbidden=string_list(data.get("forbidden")),
        transfer_conditions=string_list(data.get("transfer_conditions")),
        self_modification_roles=string_list(data.get("self_modification_roles")),
    )


def procedure_from_json(data: dict[str, Any] | None) -> VerifierProcedure | None:
    if data is None:
        return None
    return VerifierProcedure(
        steps=string_list(data.get("steps")),
        tests=string_list(data.get("tests")),
        proof_obligations=string_list(data.get("proof_obligations")),
        statistical_methods=string_list(data.get("statistical_methods")),
        stochastic_methods=string_list(data.get("stochastic_methods")),
        tool_dependencies=string_list(data.get("tool_dependencies")),
        evaluator_versions=string_list(data.get("evaluator_versions")),
        counterexample_search=string_list(data.get("counterexample_search")),
        boundary_checks=string_list(data.get("boundary_checks")),
    )


def certification_condition_from_json(
    data: dict[str, Any] | None,
) -> CertificationCondition | None:
    if data is None:
        return None
    return CertificationCondition(
        pass_conditions=string_list(data.get("pass_conditions")),
        fail_conditions=string_list(data.get("fail_conditions")),
        quarantine_conditions=string_list(data.get("quarantine_conditions")),
        residualization_conditions=string_list(data.get("residualization_conditions")),
        promotion_conditions=string_list(data.get("promotion_conditions")),
    )


def boundary_refs_from_json(data: dict[str, Any] | None) -> BoundaryRefs | None:
    if data is None:
        return None
    return BoundaryRefs(
        destructive_boundary_ref=str(data.get("destructive_boundary_ref", "")),
        narrowing_boundary_ref=str(data.get("narrowing_boundary_ref", "")),
        reachability_certificate_refs=string_list(data.get("reachability_certificate_refs")),
        inherited_boundary_refs=string_list(data.get("inherited_boundary_refs")),
    )


def residual_hooks_from_json(data: dict[str, Any] | None) -> ResidualHooks | None:
    if data is None:
        return None
    return ResidualHooks(
        unresolved_residual_refs=string_list(data.get("unresolved_residual_refs")),
        missing_core_fields=string_list(data.get("missing_core_fields")),
        missing_fields=string_list(data.get("missing_fields")),
        conflict_residual_refs=string_list(data.get("conflict_residual_refs")),
        merge_loss_residual_refs=string_list(data.get("merge_loss_residual_refs")),
        redaction_residual_refs=string_list(data.get("redaction_residual_refs")),
    )


def update_profile_from_json(data: dict[str, Any] | None) -> UpdateProfile | None:
    if data is None:
        return None
    return UpdateProfile(
        repair_conditions=string_list(data.get("repair_conditions")),
        retirement_conditions=string_list(data.get("retirement_conditions")),
        revalidation_triggers=string_list(data.get("revalidation_triggers")),
        scope_drift_triggers=string_list(data.get("scope_drift_triggers")),
        contamination_triggers=string_list(data.get("contamination_triggers")),
        rollback_hooks=string_list(data.get("rollback_hooks")),
    )


def circulation_status_from_json(data: dict[str, Any] | None) -> CirculationStatus | None:
    if data is None:
        return None
    return CirculationStatus(
        visibility=Visibility(str(data.get("visibility", Visibility.PRIVATE))),
        trust_status=TrustStatus(str(data.get("trust_status", TrustStatus.LOCAL))),
        local_internalization_status=str(data.get("local_internalization_status", "local")),
        quarantine_ref=str(data.get("quarantine_ref", "")),
        translation_residual_refs=string_list(data.get("translation_residual_refs")),
        redaction_residual_refs=string_list(data.get("redaction_residual_refs")),
        boundary_check_refs=string_list(data.get("boundary_check_refs")),
    )


def anti_overclosure_from_json(data: dict[str, Any] | None) -> AntiOverclosure:
    if data is None:
        return AntiOverclosure()
    return AntiOverclosure(
        unknowns_to_preserve=string_list(data.get("unknowns_to_preserve")),
        future_candidates_may_narrow=bool(data.get("future_candidates_may_narrow", False)),
        question_forms_may_suppress=bool(data.get("question_forms_may_suppress", False)),
        schema_overclosure_residuals=string_list(data.get("schema_overclosure_residuals")),
        lineage_laundering_checks=string_list(data.get("lineage_laundering_checks")),
    )


def ecological_invariants_from_json(data: dict[str, Any] | None) -> EcologicalInvariants:
    if data is None:
        return EcologicalInvariants()
    return EcologicalInvariants(
        preserve_origin=bool(data.get("preserve_origin", True)),
        preserve_scope=bool(data.get("preserve_scope", True)),
        preserve_residuals=bool(data.get("preserve_residuals", True)),
        preserve_boundaries=bool(data.get("preserve_boundaries", True)),
        preserve_counter_packet_route=bool(data.get("preserve_counter_packet_route", True)),
        preserve_aperture=bool(data.get("preserve_aperture", True)),
    )


def residual_liveness_from_json(data: dict[str, Any] | None) -> ResidualLivenessPolicy:
    if data is None:
        return ResidualLivenessPolicy()
    return ResidualLivenessPolicy(
        owner=str(data.get("owner", "")),
        deadline=str(data.get("deadline", "")),
        resource_quota=string_list(data.get("resource_quota")),
        recheck_trigger=str(data.get("recheck_trigger", "")),
        preserved_unknown_route=str(data.get("preserved_unknown_route", "")),
    )


def residual_route_from_json(data: Any) -> ResidualRoute | None:
    if data is None:
        return None
    data = as_dict(data, name="residual route")
    return ResidualRoute(
        owner=str(data.get("owner", "")),
        deadline=str(data.get("deadline", "")),
        resource_quota=string_tuple(data.get("resource_quota")),
        recheck_trigger=str(data.get("recheck_trigger", "")),
        route_type=ResidualMetabolismRoute(
            str(data.get("route_type", ResidualMetabolismRoute.EXPLICIT_PRESERVED_UNKNOWN))
        ),
        authority_effect=str(data.get("authority_effect", "informational")),
        active_follow_through=bool(data.get("active_follow_through", True)),
    )


def residual_from_json(data: Any) -> ResidualRecord:
    data = as_dict(data, name="residual")
    return ResidualRecord(
        kind=ResidualKind(str(data.get("kind", ResidualKind.UNRESOLVED))),
        origin=str(data.get("origin", "")),
        scope=string_tuple(data.get("scope")),
        obligation=str(data.get("obligation", "")),
        payload=dict_value(data.get("payload"), name="payload"),
        exposure=str(data.get("exposure", "informational")),
        status=LedgerStatus(str(data.get("status", LedgerStatus.ACTIVE))),
        route=residual_route_from_json(data.get("route")),
        update_links=string_tuple(data.get("update_links")),
        provenance=string_tuple(data.get("provenance")),
        residual_id=str(data.get("residual_id") or new_id("res")),
    )


def sound_gap_residual_from_json(data: Any) -> SoundGapResidual:
    data = as_dict(data, name="sound gap residual")
    base = residual_from_json(data)
    return SoundGapResidual(
        kind=ResidualKind.SOUNDNESS_GAP,
        origin=base.origin,
        scope=base.scope,
        obligation=base.obligation,
        payload=base.payload,
        exposure=base.exposure,
        status=base.status,
        route=base.route,
        update_links=base.update_links,
        provenance=base.provenance,
        residual_id=base.residual_id,
        certificate_ref=str(data.get("certificate_ref", "")),
        semantic_target=str(data.get("semantic_target", "")),
        operational_claim=str(data.get("operational_claim", "")),
    )


def counterexample_channel_from_json(data: Any) -> CounterexampleChannel:
    data = as_dict(data, name="counterexample channel")
    return CounterexampleChannel(
        channel_id=str(data.get("channel_id", "")),
        target_ref=str(data.get("target_ref", "")),
        status=LifecycleStatus(str(data.get("status", LifecycleStatus.ACTIVE))),
        last_checked=str(data.get("last_checked", "")),
        search_window=str(data.get("search_window", "")),
        budget=string_tuple(data.get("budget")),
        freshness_interval=str(data.get("freshness_interval", "")),
        unresolved_reports=string_tuple(data.get("unresolved_reports")),
        stale_condition=str(data.get("stale_condition", "")),
        adversarial_ingress=string_tuple(data.get("adversarial_ingress")),
        cex_closed_result=str(data.get("cex_closed_result", "not_checked")),
        residual_obligations=string_tuple(data.get("residual_obligations")),
    )


def reachability_certificate_from_json(data: Any) -> ReachabilityCertificate:
    data = as_dict(data, name="reachability certificate")
    cex_data = data.get("cex_channel", {})
    return ReachabilityCertificate(
        certificate_id=str(data.get("certificate_id", "")),
        object_id=str(data.get("object_id", "")),
        schema_version=str(data.get("schema_version", "")),
        canonical_digest=digest_from_json(data.get("canonical_digest")),
        status=LifecycleStatus(str(data.get("status", LifecycleStatus.ACTIVE))),
        predicate=str(data.get("predicate", "")),
        certificate_contract=str(data.get("certificate_contract", "")),
        carrier_id=str(data.get("carrier_id", "")),
        carrier_acceptance_judgment_ref=str(data.get("carrier_acceptance_judgment_ref", "")),
        carrier_type=str(data.get("carrier_type", "")),
        concretization_id=str(data.get("concretization_id", "")),
        checker_id=str(data.get("checker_id", "")),
        checker_acceptance_judgment_ref=str(data.get("checker_acceptance_judgment_ref", "")),
        checker_result=str(data.get("checker_result", "")),
        claim_kind=str(data.get("claim_kind", "")),
        coverage_statement=str(data.get("coverage_statement", "")),
        cover_check_result=str(data.get("cover_check_result", "")),
        empty_concretization_statement=str(data.get("empty_concretization_statement", "")),
        empty_check_result=str(data.get("empty_check_result", "")),
        cex_channel=counterexample_channel_from_json(cex_data),
        soundness_target=str(data.get("soundness_target", "")),
        operational_claim_basis=string_tuple(data.get("operational_claim_basis")),
        soundgap_residuals=tuple(
            sound_gap_residual_from_json(item) for item in data.get("soundgap_residuals", ())
        ),
        assumptions=string_tuple(data.get("assumptions")),
        scope=string_tuple(data.get("scope")),
        horizon=str(data.get("horizon", "")),
        resource_bounds=string_tuple(data.get("resource_bounds")),
        cost_bounds=string_tuple(data.get("cost_bounds")),
        latency_bounds=string_tuple(data.get("latency_bounds")),
        invalidation_conditions=string_tuple(data.get("invalidation_conditions")),
        recheck_trigger=str(data.get("recheck_trigger", "")),
        migration_witness_ref=str(data.get("migration_witness_ref", "")),
        falsification_attempts=string_tuple(data.get("falsification_attempts")),
        open_counterexample_residuals=string_tuple(data.get("open_counterexample_residuals")),
        residual_obligations=string_tuple(data.get("residual_obligations")),
        provenance=string_tuple(data.get("provenance")),
    )


def ledger_event_from_json(data: Any) -> LedgerEvent:
    data = as_dict(data, name="ledger event")
    predecessor = data.get("predecessor_event_id")
    return LedgerEvent(
        kind=str(data.get("kind", "import")),
        source_residuals=string_tuple(data.get("source_residuals")),
        target_residuals=string_tuple(data.get("target_residuals")),
        justification=str(data.get("justification", "imported event")),
        pre_state_digest=str(data.get("pre_state_digest", "")),
        post_state_digest=str(data.get("post_state_digest", "")),
        actor_authority_ref=str(data.get("actor_authority_ref", "import")),
        policy_id=str(data.get("policy_id", "vet-ledger-policy-v1")),
        event_id=str(data.get("event_id") or new_id("le")),
        clock_model=str(data.get("clock_model", "total_order")),
        conflict_policy=str(data.get("conflict_policy", "preserve_or_residualize")),
        predecessor_event_id=str(predecessor) if predecessor is not None else None,
        provenance=string_tuple(data.get("provenance")),
        event_payload=dict_value(data.get("event_payload"), name="event_payload"),
    )


def ledger_from_json(data: Any) -> ResidualLedger:
    data = as_dict(data, name="ledger")
    ledger = ResidualLedger(policy_id=str(data.get("policy_id", "vet-ledger-policy-v1")))
    residuals = data.get("residuals", [])
    if isinstance(residuals, dict):
        items = list(residuals.values())
    elif isinstance(residuals, list | tuple):
        items = list(residuals)
    else:
        raise ValueError("ledger residuals must be an object or list")
    for item in items:
        residual = residual_from_json(item)
        ledger.residuals[residual.residual_id] = residual
    events = data.get("events", [])
    if not isinstance(events, list | tuple):
        raise ValueError("ledger events must be a list")
    ledger.events = [ledger_event_from_json(item) for item in events]
    return ledger


def history_from_json(data: Any) -> ObservableProcessHistory:
    if not isinstance(data, dict):
        return ObservableProcessHistory()
    events = data.get("events", [])
    if not isinstance(events, list | tuple):
        return ObservableProcessHistory()
    history = ObservableProcessHistory()
    for item in events:
        if not isinstance(item, dict):
            continue
        predecessor = item.get("predecessor_event_id")
        payload = item.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        history.events.append(
            HistoryEvent(
                event_type=str(item.get("event_type", "unknown")),
                payload=payload,
                event_id=str(item.get("event_id", "")),
                predecessor_event_id=str(predecessor) if predecessor is not None else None,
                provenance=string_tuple(item.get("provenance")),
            )
        )
    return history


def ecology_state_from_json(data: Any) -> VerifierEcologyState:
    if not isinstance(data, dict):
        state = VerifierEcologyState()
        state.archive["json_store_snapshot"] = data
        return state

    state = VerifierEcologyState()
    state.history = history_from_json(data.get("history", {}))

    population = data.get("packet_population", {})
    if isinstance(population, dict):
        for packet_data in population.values():
            packet = packet_from_json(packet_data)
            state.packet_population[packet.packet_id] = packet

    ledger_data = data.get("residual_ledger")
    if isinstance(ledger_data, dict):
        state.residual_ledger = ledger_from_json(ledger_data)

    archive = data.get("archive")
    if isinstance(archive, dict):
        state.archive = archive
    capital = data.get("reusable_intelligence_capital")
    if isinstance(capital, dict):
        state.reusable_intelligence_capital = capital
    return state
