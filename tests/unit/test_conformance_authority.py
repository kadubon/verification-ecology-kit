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


def test_conformance_operational_checks_authority_support() -> None:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"status": "active"})
    envelope.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [envelope],
        authority_decisions=[
            {
                "authority_decision_id": "a",
                "decision": "allow",
                "lifecycle_status": "active",
                "required_support_refs": ["support"],
                "support_judgment_refs": [],
            }
        ],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    bundle.authority_decisions[0]["support_judgment_refs"] = ["judgment"]
    assert ConformanceEngine().run(bundle).decision.value == "accept"


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
