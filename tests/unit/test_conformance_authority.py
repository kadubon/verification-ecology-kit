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
from verification_ecology_kit.references import ObjectEnvelope, SchemaCatalogue


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
