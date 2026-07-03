from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

import verification_ecology_kit.serde as public_serde
from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model import serde
from verification_ecology_kit.model.aperture import Aperture, ApertureComparison, CapacityRecord
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.ledger import LedgerEvent, ResidualLedger, TraceCertificate
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    ConformanceProfile,
    LifecycleStatus,
    ResidualKind,
)
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute
from verification_ecology_kit.model.semantics import (
    AuthorityEligibility,
    EcologyEligibility,
    SemanticCheckReport,
    SemanticLevel,
    SupportEligibility,
)
from verification_ecology_kit.references import (
    ObjectEnvelope,
    ObjectRef,
    SchemaCatalogue,
    SupportReferenceResolver,
    resolve_authority_ref,
    resolve_support_ref,
)
from verification_ecology_kit.result import FailureCode, fail_result, pass_result, residual_result
from verification_ecology_kit.runtime.json_store import _reject_symlink_target


def test_semantic_report_profiles_and_outcomes() -> None:
    report = SemanticCheckReport.from_results(
        profile=ConformanceProfile.FEDERATED,
        ordered_check_results=[
            pass_result("SchemaOK"),
            residual_result("RefGraphOK", FailureCode.UNRESOLVED_REFERENCE, residual_refs=("r",)),
            fail_result("AuthorityOK", FailureCode.AUTHORITY_MISMATCH, residual_refs=("a",)),
            residual_result("EcologyOK", FailureCode.RESIDUAL_NOT_LIVE, residual_refs=("e",)),
        ],
    )

    assert SemanticLevel.AUTHORITY in report.failed_levels
    assert report.support_valid == SupportEligibility.ELIGIBLE_WITH_RESIDUALS
    assert report.evidence_valid == SupportEligibility.NOT_CHECKED
    assert report.authority_valid == AuthorityEligibility.BLOCKED
    assert report.ecology_valid == EcologyEligibility.COHERENT_WITH_RESIDUALS
    assert not report.required_levels_passed
    assert report.to_dict()["complete_formal_semantics_claim"] is False
    assert (
        SemanticCheckReport.from_results(
            profile=ConformanceProfile.OPERATIONAL,
            ordered_check_results=[],
        ).record_valid
        is False
    )


def test_stable_serde_loaders_cover_bundle_contracts_and_aperture() -> None:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    envelope.refresh_digest()
    assert serde.load_object_envelope(envelope) is envelope
    assert public_serde.load_digest("abc") == Digest("sha256", "abc")

    ref_payload = envelope.ref(bundle_id="b").to_dict()
    catalogue = serde.load_schema_catalogue(
        {
            "catalogue_id": "cat",
            "schemas": {"schema": {"type": "object"}},
            "migration_witnesses": {"schema->2.0": "mw"},
        },
        objects=[envelope],
    )
    assert catalogue.migration_witnesses[("schema", "2.0")] == "mw"

    decision = serde.load_authority_decision(
        {
            "authority_decision_id": "auth",
            "object_id": "o",
            "schema_version": "1",
            "canonical_digest": envelope.canonical_digest.to_dict(),
            "lifecycle_status": "active",
            "policy_id": "p",
            "action": "deployment",
            "decision": "allow",
            "support_statuses": {"s": "stale"},
            "required_human_assessment_roles": ["reviewer"],
            "required_tool_assessment_roles": ["scanner"],
        }
    )
    assert decision.support_statuses == {"s": LifecycleStatus.STALE}

    registry = serde.load_contract_registry(
        {
            "carrier_contracts": [
                {
                    "contract_id": "carrier",
                    "kind": "json",
                    "domain": "a",
                    "codomain": "b",
                    "accepted_versions": ["1"],
                }
            ],
            "checker_contracts": {
                "checker": {
                    "contract_id": "checker",
                    "checker_type": "policy",
                    "accepted_versions": ["1"],
                    "accepted_statuses": ["active"],
                }
            },
            "judgment_contracts": [
                {
                    "judgment_kind": "support",
                    "subject_type": "schema",
                    "checker_or_policy_type": "checker",
                    "version": "1",
                }
            ],
        }
    )
    assert "carrier" in registry.carrier_contracts
    assert "checker" in registry.checker_contracts
    assert "support" in registry.judgment_contracts

    bundle = serde.load_vet_bundle(
        {
            "bundle_id": "b",
            "schema_version": "1",
            "conformance_profile": "core",
            "objects": [{**envelope.to_dict(), "status_ref": None}],
            "references": [ref_payload],
            "schema_catalogue": catalogue.__dict__,
            "residual_ledger": {"residuals": [], "events": []},
            "authority_decisions": [{"decision": "deny"}],
            "judgment_records": [{"jvalid_result": "not_checked"}],
        }
    )
    assert bundle.objects[0].object_id == "o"
    assert bundle.authority_decisions[0]["decision"] == "deny"
    assert serde.load_audit_state({"packets": [bundle.objects[0].payload]}).packet_population

    narrowed = Aperture(
        question_form_capacity=CapacityRecord(
            "question",
            feasible_capacity=1,
            inert_residual_obligations=("expired",),
        )
    )
    before = Aperture(question_form_capacity=CapacityRecord("question", feasible_capacity=2))
    assert before.compare(narrowed) == ApertureComparison.NARROWED_WITH_INERT_RESIDUAL
    assert serde.load_aperture(narrowed.to_dict()).question_form_capacity.has_debt()


def test_residual_ledger_trace_checks_delta_certificates_and_preservation() -> None:
    ledger = ResidualLedger()
    residual = ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route")
    add_event = ledger.add(residual)
    assert "pre_residuals" in add_event.event_payload
    assert "delta" in add_event.event_payload
    assert ledger.trace_ok().passed

    missing_preservation = ResidualLedger()
    missing_preservation.add(ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route"))
    payload = dict(missing_preservation.events[0].event_payload)
    payload.pop("preservation_reasons", None)
    missing_preservation.events[0] = replace(
        missing_preservation.events[0],
        event_payload=payload,
    )
    assert not missing_preservation.trace_ok().passed

    partial = ResidualLedger()
    partial.add(
        ResidualRecord(
            ResidualKind.UNRESOLVED,
            "o",
            ("s",),
            "route",
            route=ResidualRoute(
                "owner",
                (datetime.now(UTC) + timedelta(days=1)).isoformat(),
                ("1h",),
                "daily",
            ),
        )
    )
    partial.events[0] = replace(partial.events[0], clock_model="partial_order")
    assert not partial.trace_ok().passed
    payload = {
        **partial.events[0].event_payload,
        "trace_certificate": TraceCertificate(
            "tc",
            "partial",
            representative_linearization_refs=("linearization",),
        ),
    }
    partial.events[0] = replace(partial.events[0], event_payload=payload)
    assert partial.trace_ok().passed

    bad_target = ResidualLedger()
    bad_target.add(ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route"))
    bad_target.events[0] = replace(bad_target.events[0], target_residuals=())
    assert not bad_target.trace_ok().passed

    retired = ResidualLedger()
    retired_residual = ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route")
    retired.add(retired_residual)
    retired.retire(retired_residual.residual_id, justification="done")
    retired.events[1] = replace(retired.events[1], justification="")
    assert not retired.trace_ok().passed

    event = LedgerEvent(
        kind="merge",
        source_residuals=("missing",),
        target_residuals=("target",),
        justification="manual",
        pre_state_digest=ResidualLedger().state_digest(),
        post_state_digest=ResidualLedger().state_digest(),
        actor_authority_ref="actor",
        policy_id="policy",
        event_payload={"post_residuals": {}},
    )
    assert event.to_dict()["kind"] == "merge"


def test_support_reference_helpers_cover_status_migration_redaction_and_gates() -> None:
    active = ObjectEnvelope("active", "schema", "1.0", {"status": "active"})
    active.refresh_digest()
    redacted = ObjectEnvelope(
        "redacted",
        "schema",
        "1.0",
        {"status": "active", "redacted": True, "redaction_residual_refs": ["rr"]},
    )
    redacted.refresh_digest()
    gated = ObjectEnvelope("gated", "schema", "1.0", {"status": "active", "residual_gates": ["g"]})
    gated.refresh_digest()
    migrated = ObjectEnvelope(
        "migrated",
        "schema",
        "2.0",
        {"status": "migrated", "migration_witness_ref": "mw"},
    )
    migrated.refresh_digest()
    status_target = ObjectEnvelope("status", "schema", "1.0", {"status": "active"})
    status_target.refresh_digest()
    status_ref = status_target.ref(bundle_id="b")
    via_status_ref = ObjectEnvelope(
        "via-status", "schema", "1.0", {"value": 1}, status_ref=status_ref
    )
    via_status_ref.refresh_digest()
    resolver = SupportReferenceResolver(
        bundle_id="b",
        envelopes=[active, redacted, gated, migrated, status_target, via_status_ref],
        schema_catalogue=SchemaCatalogue("cat", {"schema": ("1.0", "2.0")}),
    )

    assert resolve_support_ref(resolver, active.ref(bundle_id="b")).check_result.passed
    assert resolve_authority_ref(resolver, migrated.ref(bundle_id="b")).check_result.passed
    assert resolver.resolve_support_ref(redacted.ref(bundle_id="b")).check_result.passed
    assert not resolver.resolve_support_ref(gated.ref(bundle_id="b")).check_result.passed
    assert resolver.resolve_support_ref(via_status_ref.ref(bundle_id="b")).status_view is not None
    assert not resolver.resolve_support_ref(ObjectRef("other", "x", "schema")).check_result.passed


def test_federated_conformance_and_json_store_symlink_option(tmp_path) -> None:
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.FEDERATED,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [],
    )
    report = ConformanceEngine().run(bundle)
    assert report.semantic_report is not None
    assert report.semantic_report["authority_valid"] == "blocked"
    assert report.semantic_report["ecology_valid"] == "coherent"

    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    _reject_symlink_target(link, allow_symlink=True)


def test_conformance_negative_semantic_branches() -> None:
    active = ObjectEnvelope("active", "schema", "1.0", {"status": "active"})
    active.refresh_digest()
    status = ObjectEnvelope(
        "status",
        "schema",
        "1.0",
        {
            "status_events": [
                {
                    "pre_status": "unknown",
                    "post_status": "active",
                    "cause": "unit",
                    "actor_authority_ref": "tester",
                    "ledger_event_ref": "ledger",
                    "status_event_id": "status-event",
                }
            ]
        },
    )
    status.refresh_digest()
    via_status = ObjectEnvelope(
        "via-status",
        "schema",
        "1.0",
        {"value": 1},
        status_ref=status.ref(bundle_id="b"),
    )
    via_status.refresh_digest()
    catalogue = SchemaCatalogue("cat", {"schema": ("1.0",)}, {"schema": {"type": "object"}})
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        catalogue,
        [active, status, via_status],
        judgment_records=[
            1,
        ],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    bundle.judgment_records = [{"jvalid_result": "not_applicable", "operational_use": True}]
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    bundle.judgment_records = [{"jvalid_result": "not_checked", "judgment_id": "j"}]
    report = ConformanceEngine().run(bundle)
    judgment = next(
        result for result in report.ordered_check_results if result.check_name == "JudgmentOK"
    )
    assert judgment.result.value == "residualize"

    bundle.judgment_records = []
    bundle.authority_decisions = [{"decision": "residualize", "residual_gates": ["gate"]}]
    authority = next(
        result
        for result in ConformanceEngine().run(bundle).ordered_check_results
        if result.check_name == "AuthorityOK"
    )
    assert authority.result.value == "residualize"

    bundle.authority_decisions = [{"decision": "allow", "deny_by_default": False}]
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    broken_status = ObjectEnvelope(
        "broken-status",
        "schema",
        "1.0",
        {"value": 1},
        status_ref=ObjectRef("b", "missing", "schema"),
    )
    broken_status.refresh_digest()
    broken_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        catalogue,
        [broken_status],
    )
    assert ConformanceEngine().run(broken_bundle).decision.value == "reject"

    stale_route = ResidualRoute(
        "owner",
        "2000-01-01T00:00:00Z",
        ("1h",),
        "daily",
        authority_effect="blocks_authority",
    )
    stale = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "o",
        ("s",),
        "route",
        route=stale_route,
    )
    ecology_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.FEDERATED,
        catalogue,
        [active],
        authority_decisions=[
            {
                "authority_decision_id": "a",
                "decision": "allow",
                "lifecycle_status": "active",
                "auth_inputs": {
                    "auth_inputs_ref": "ai",
                    "object_id": "active",
                    "schema_version": "1",
                    "canonical_digest": active.canonical_digest.to_dict(),
                    "candidate_ref": "active",
                    "action": "local_use",
                },
            }
        ],
    )
    ecology_bundle.residual_ledger.add(stale)
    ecology = next(
        result
        for result in ConformanceEngine().run(ecology_bundle).ordered_check_results
        if result.check_name == "EcologyOK"
    )
    assert ecology.result.value == "residualize"


def test_authority_engine_and_trace_certificate_dict_branches() -> None:
    from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine

    decision = AuthorityDecision(
        authority_decision_id="a",
        object_id="o",
        schema_version="1",
        canonical_digest=Digest("sha256", "abc"),
        lifecycle_status=LifecycleStatus.ACTIVE,
        policy_id="p",
        action=AuthorityAction.DEPLOYMENT,
        decision=AuthorityDecisionValue.ALLOW,
        support_statuses={"support": LifecycleStatus.REVOKED},
        required_human_assessment_roles=("human",),
        required_tool_assessment_roles=("tool",),
        sandbox_required=True,
        sandbox_status="inactive",
        expiry_state="expired",
    )
    _, result = AuthorityEngine().aggregate(AuthorityAction.DEPLOYMENT, [decision])
    assert not result.passed
    assert "support" in result.residual_refs

    routed = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "o",
        ("s",),
        "route",
        route=ResidualRoute(
            "owner",
            (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            ("1h",),
            "daily",
        ),
    )
    ledger = ResidualLedger()
    ledger.add(routed)
    payload = {
        **ledger.events[0].event_payload,
        "trace_certificate": {
            "trace_certificate_id": "tc",
            "trace_semantics": "partial",
            "representative_linearization_refs": ["linear"],
            "commutation_evidence_refs": ["commute"],
            "conflict_residual_refs": ["conflict"],
            "residual_obligations": ["residual"],
        },
    }
    ledger.events[0] = replace(
        ledger.events[0],
        clock_model="partial_order",
        event_payload=payload,
    )
    assert ledger.trace_ok().passed

    no_payload = ResidualLedger()
    no_payload.add(routed)
    no_payload.events[0] = replace(no_payload.events[0], event_payload={})
    assert not no_payload.trace_ok().passed
