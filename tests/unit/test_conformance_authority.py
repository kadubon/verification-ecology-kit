from __future__ import annotations

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine
from verification_ecology_kit.model.certification import (
    CertificationEngine,
    CertificationProfile,
    CertificationRecord,
)
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    ConformanceProfile,
    LifecycleStatus,
)
from verification_ecology_kit.references import ObjectEnvelope, ObjectRef, SchemaCatalogue


def _bundle() -> VetBundle:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"value": "x"})
    envelope.refresh_digest()
    return VetBundle(
        bundle_id="b",
        schema_version="1",
        conformance_profile=ConformanceProfile.CORE,
        schema_catalogue=SchemaCatalogue("cat", {"schema": ("1.0",)}),
        objects=[envelope],
    )


def test_conformance_core_accepts_valid_digest_bundle() -> None:
    report = ConformanceEngine().run(_bundle())
    assert report.decision.value == "accept"
    assert [result.check_name for result in report.ordered_check_results] == [
        "SchemaOK",
        "DigestPolicyOK",
        "ObjectDigestOK",
        "BundleDigestOK",
        "RefGraphOK",
        "ResidualOK",
    ]


def test_conformance_core_rejects_schema_digest_bundle_and_reference_gaps() -> None:
    unsupported = ObjectEnvelope("o", "schema", "2.0", {"value": "x"})
    unsupported.refresh_digest()
    unsupported_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.CORE,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [unsupported],
    )
    assert ConformanceEngine().run(unsupported_bundle).decision.value == "reject"

    invalid_payload = ObjectEnvelope("o", "schema", "1.0", {"value": 1})
    invalid_payload.refresh_digest()
    invalid_schema_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.CORE,
        SchemaCatalogue(
            "cat",
            {"schema": ("1.0",)},
            schemas={"schema": {"type": "object", "properties": {"value": {"type": "string"}}}},
        ),
        [invalid_payload],
    )
    assert ConformanceEngine().run(invalid_schema_bundle).decision.value == "reject"

    missing_digest = ObjectEnvelope("o", "schema", "1.0", {"value": "x"})
    missing_digest_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.CORE,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [missing_digest],
    )
    assert ConformanceEngine().run(missing_digest_bundle).decision.value == "reject"

    duplicate = ObjectEnvelope("o", "schema", "1.0", {"value": "x"})
    duplicate.refresh_digest()
    duplicate_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.CORE,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [duplicate, duplicate],
    )
    assert ConformanceEngine().run(duplicate_bundle).decision.value == "reject"

    ref_bundle = _bundle()
    ref_bundle.references.append(ObjectRef("b", "missing", "schema"))
    assert ConformanceEngine().run(ref_bundle).decision.value == "reject"


def test_conformance_operational_uses_status_ref() -> None:
    status = ObjectEnvelope("status", "status-event", "1.0", {"status": "active"})
    status.refresh_digest()
    envelope = ObjectEnvelope(
        "o",
        "schema",
        "1.0",
        {"value": "x"},
        status_ref=ObjectRef("b", "status", "status-event", "/payload"),
    )
    envelope.refresh_digest()
    bundle = VetBundle(
        bundle_id="b",
        schema_version="1",
        conformance_profile=ConformanceProfile.OPERATIONAL,
        schema_catalogue=SchemaCatalogue(
            "cat",
            {"schema": ("1.0",), "status-event": ("1.0",)},
        ),
        objects=[envelope, status],
    )

    assert ConformanceEngine().run(bundle).decision.value == "accept"


def test_conformance_operational_rejects_empty_bundle() -> None:
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [],
    )
    report = ConformanceEngine().run(bundle)
    assert report.decision.value == "reject"
    assert report.ordered_check_results[0].check_name == "OperationalBundleNonEmpty"


def test_conformance_status_fold_blocks_stale_event() -> None:
    envelope = ObjectEnvelope(
        "o",
        "schema",
        "1.0",
        {
            "status_events": [
                {
                    "status_event_id": "s1",
                    "object_id": "o",
                    "pre_status": "active",
                    "post_status": "stale",
                    "cause": "counterexample",
                    "actor_authority_ref": "auth",
                    "ledger_event_ref": "le",
                }
            ]
        },
    )
    envelope.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [envelope],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"


def test_conformance_status_fold_residualizes_invalid_or_missing_status() -> None:
    invalid_event = ObjectEnvelope(
        "o",
        "schema",
        "1.0",
        {
            "status_events": [
                {
                    "object_id": "o",
                    "pre_status": "active",
                    "post_status": "not-a-status",
                    "cause": "bad event",
                    "actor_authority_ref": "auth",
                    "ledger_event_ref": "le",
                }
            ]
        },
    )
    invalid_event.refresh_digest()
    invalid_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [invalid_event],
    )
    assert ConformanceEngine().run(invalid_bundle).decision.value == "reject"

    missing_status = ObjectEnvelope("o", "schema", "1.0", {"value": "x"})
    missing_status.refresh_digest()
    missing_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [missing_status],
    )
    assert ConformanceEngine().run(missing_bundle).decision.value == "reject"


def test_conformance_operational_rejects_stale_status_and_unchecked_judgment() -> None:
    stale = ObjectEnvelope("o", "schema", "1.0", {"status": "stale"})
    stale.refresh_digest()
    stale_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [stale],
    )
    assert ConformanceEngine().run(stale_bundle).decision.value == "reject"

    active = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    active.refresh_digest()
    judgment_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [active],
        judgment_records=[{"judgment_id": "j", "jvalid_result": "not_checked"}],
    )
    assert ConformanceEngine().run(judgment_bundle).decision.value == "reject"


def test_conformance_judgment_equivalence_fields_are_enforced() -> None:
    active = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    active.refresh_digest()
    base = {
        "judgment_id": "j",
        "jvalid_result": "pass",
        "contract_version": "v1",
        "expected_contract_version": "v2",
        "input_digest": "abc",
        "result": "pass",
        "allowed_results": ["pass"],
    }
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [active],
        judgment_records=[base],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    base["expected_contract_version"] = "v1"
    base["expected_input_digest"] = "def"
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    base["expected_input_digest"] = "abc"
    base["allowed_results"] = ["fail"]
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    base["allowed_results"] = ["pass"]
    base["jvalid_result"] = "not_applicable"
    assert ConformanceEngine().run(bundle).decision.value == "accept"


def test_conformance_operational_checks_authority_support() -> None:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    support = ObjectEnvelope("support", "schema", "1.0", {"status": "active", "value": "ok"})
    support.refresh_digest()
    envelope.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [envelope, support],
        authority_decisions=[
            {
                "authority_decision_id": "a",
                "decision": "allow",
                "lifecycle_status": "active",
                "required_support_refs": ["support"],
                "auth_inputs": {
                    "auth_inputs_ref": "ai",
                    "object_id": "o",
                    "schema_version": "1",
                    "canonical_digest": envelope.canonical_digest.to_dict(),
                    "candidate_ref": "o",
                    "action": "local_use",
                    "support_refs": ["support"],
                },
                "support_judgment_refs": [],
            }
        ],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    bundle.authority_decisions[0]["support_judgment_refs"] = ["judgment"]
    assert ConformanceEngine().run(bundle).decision.value == "accept"


def test_conformance_authority_rejects_stale_and_residual_gated_allow() -> None:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    support = ObjectEnvelope("support", "schema", "1.0", {"status": "active", "value": "ok"})
    support.refresh_digest()
    envelope.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [envelope, support],
        authority_decisions=[
            {
                "authority_decision_id": "a",
                "decision": "allow",
                "deny_by_default": True,
                "lifecycle_status": "active",
                "required_support_refs": ["support"],
                "support_judgment_refs": ["judgment"],
                "auth_inputs": {
                    "auth_inputs_ref": "ai",
                    "object_id": "o",
                    "schema_version": "1",
                    "canonical_digest": envelope.canonical_digest.to_dict(),
                    "candidate_ref": "o",
                    "action": "local_use",
                    "support_refs": ["support"],
                },
                "support_statuses": {"support": "stale"},
                "residual_gates": ["residual-open"],
            }
        ],
    )

    report = ConformanceEngine().run(bundle)

    assert report.decision.value == "reject"
    authority = next(
        result for result in report.ordered_check_results if result.check_name == "AuthorityOK"
    )
    assert set(authority.residual_refs) == {"support", "residual-open"}


def test_conformance_authority_residualize_and_deny_paths() -> None:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    envelope.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [envelope],
        authority_decisions=[
            {"authority_decision_id": "a", "decision": "residualize", "residual_gates": ["r"]}
        ],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    bundle.authority_decisions = [
        {"authority_decision_id": "a", "decision": "allow", "deny_by_default": False}
    ]
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    bundle.authority_decisions = [
        {
            "authority_decision_id": "a",
            "decision": "allow",
            "support_judgment_refs": ["j"],
            "action": "unknown-action",
            "active_decision_record": False,
        }
    ]
    assert ConformanceEngine().run(bundle).decision.value == "reject"


def test_authority_denies_by_default() -> None:
    decision, result = AuthorityEngine().aggregate(AuthorityAction.DEPLOYMENT, [])
    assert decision == AuthorityDecisionValue.DENY
    assert not result.passed


def test_authority_allows_only_active_matching_support() -> None:
    auth = AuthorityDecision(
        authority_decision_id="a1",
        object_id="obj",
        schema_version="1",
        canonical_digest=Digest("sha256", "abc"),
        lifecycle_status=LifecycleStatus.ACTIVE,
        policy_id="p",
        action=AuthorityAction.LOCAL_USE,
        decision=AuthorityDecisionValue.ALLOW,
        required_support_refs=("support-1",),
    )
    decision, result = AuthorityEngine().aggregate(
        AuthorityAction.LOCAL_USE,
        [auth],
        required_support_refs=("support-1",),
    )
    assert decision == AuthorityDecisionValue.ALLOW
    assert result.passed


def test_authority_denies_stale_migrated_unresolved_and_expired_support() -> None:
    auth = AuthorityDecision(
        authority_decision_id="a1",
        object_id="obj",
        schema_version="1",
        canonical_digest=Digest("sha256", "abc"),
        lifecycle_status=LifecycleStatus.ACTIVE,
        policy_id="p",
        action=AuthorityAction.DEPLOYMENT,
        decision=AuthorityDecisionValue.ALLOW,
        required_support_refs=("support-1",),
        support_statuses={"support-1": LifecycleStatus.STALE},
        migrated_without_witness_refs=("migration",),
        unresolved_support_refs=("unresolved",),
        expired_cex_closed_refs=("cex",),
        non_live_soundgap_refs=("soundgap",),
        expiry_state="expired",
    )

    decision, result = AuthorityEngine().aggregate(
        AuthorityAction.DEPLOYMENT,
        [auth],
        required_support_refs=("support-1",),
    )

    assert decision == AuthorityDecisionValue.DENY
    assert set(result.residual_refs) >= {"support-1", "migration", "unresolved", "cex", "soundgap"}


def test_certification_promotion_detects_silent_removal() -> None:
    earlier = CertificationRecord(
        "c0",
        "obj",
        "1",
        Digest("sha256", "abc"),
        LifecycleStatus.ACTIVE,
        "stable",
        "policy",
        ("scope-a",),
        "short",
        "cont",
        ("packet",),
        CertificationProfile(),
        residual_obligations=("residual-a",),
    )
    later = CertificationRecord(
        "c1",
        "obj",
        "1",
        Digest("sha256", "def"),
        LifecycleStatus.ACTIVE,
        "stable",
        "policy",
        ("scope-a", "scope-b"),
        "long",
        "cont",
        ("packet",),
        CertificationProfile(),
        residual_obligations=(),
    )
    assert not CertificationEngine().promotion_check(earlier, later).passed
