from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from verification_ecology_kit.model.aperture import Aperture, ApertureComparison, CapacityRecord
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.frontier import (
    FrontierComparison,
    FrontierEntry,
    VerifiableFrontierProfile,
)
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.records import (
    ConformanceProfile,
    ResidualKind,
    ResidualMetabolismRoute,
)
from verification_ecology_kit.model.residuals import (
    ResidualRecord,
    ResidualRoute,
    check_residual_liveness,
)
from verification_ecology_kit.references import (
    ObjectEnvelope,
    ObjectRef,
    SchemaCatalogue,
    SupportReferenceResolver,
)
from verification_ecology_kit.runtime import json_store


def _active_envelope(object_id: str = "o") -> ObjectEnvelope:
    envelope = ObjectEnvelope(object_id, "schema", "1.0", {"status": "active", "value": object_id})
    envelope.refresh_digest()
    return envelope


def test_reconstructed_jvalid_overrides_declared_pass() -> None:
    subject = _active_envelope("subject")
    ref = subject.ref(bundle_id="b")
    context = {
        "subject_ref": ref.to_dict(),
        "resolved_input_ref": ref.to_dict(),
        "canonical_input_ref": ref.to_dict(),
        "input_digest": subject.canonical_digest.to_dict(),
        "digest_algorithm_id": "sha256",
    }
    contract = {
        "judgment_kind": "support",
        "subject_type": "schema",
        "input_digest_type": "object_digest",
        "checker_or_policy_type": "checker",
        "result_type": "check_result",
        "allowed_results": ["pass"],
        "version": "2",
    }
    record = {
        "judgment_id": "j",
        "judgment_kind": "support",
        "subject": ref.to_dict(),
        "checker_or_policy_ref": "checker",
        "contract_version": "1",
        "schema_version": "1",
        "object_id": "subject",
        "canonical_digest": subject.canonical_digest.to_dict(),
        "use_context_ref": "u",
        "use_context": context,
        "contract": contract,
        "canonical_input_ref": ref.to_dict(),
        "input_pointer": "",
        "input_digest": subject.canonical_digest.to_dict(),
        "digest_algorithm_id": "sha256",
        "result": "pass",
        "jvalid_result": "pass",
        "status": "active",
    }
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [subject],
        judgment_records=[record],
    )

    report = ConformanceEngine().run(bundle)

    assert report.decision.value == "reject"


def test_authority_allow_is_derived_from_stale_support_evidence() -> None:
    candidate = _active_envelope("candidate")
    support = ObjectEnvelope("support", "schema", "1.0", {"status": "stale"})
    support.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [candidate, support],
        authority_decisions=[
            {
                "authority_decision_id": "a",
                "decision": "allow",
                "lifecycle_status": "active",
                "support_judgment_refs": ["j"],
                "auth_inputs": {
                    "auth_inputs_ref": "ai",
                    "object_id": "candidate",
                    "schema_version": "1",
                    "canonical_digest": candidate.canonical_digest.to_dict(),
                    "candidate_ref": "candidate",
                    "action": "local_use",
                    "support_refs": ["support"],
                },
            }
        ],
    )

    report = ConformanceEngine().run(bundle)
    authority = next(
        result for result in report.ordered_check_results if result.check_name == "AuthorityOK"
    )

    assert report.decision.value == "reject"
    assert "support" in authority.residual_refs


def test_support_resolver_distinguishes_support_eligibility() -> None:
    active = _active_envelope("active")
    stale = ObjectEnvelope("stale", "schema", "1.0", {"status": "stale"})
    stale.refresh_digest()
    migrated = ObjectEnvelope("migrated", "schema", "1.0", {"status": "migrated"})
    migrated.refresh_digest()
    redacted = ObjectEnvelope("redacted", "schema", "1.0", {"status": "active", "redacted": True})
    redacted.refresh_digest()
    resolver = SupportReferenceResolver(
        bundle_id="b",
        envelopes=[active, stale, migrated, redacted],
        schema_catalogue=SchemaCatalogue("cat", {"schema": ("1.0",)}),
    )

    assert resolver.resolve_support(active.ref(bundle_id="b")).check_result.passed
    assert not resolver.resolve_support(stale.ref(bundle_id="b")).check_result.passed
    assert not resolver.resolve_support(migrated.ref(bundle_id="b")).check_result.passed
    assert not resolver.resolve_support(redacted.ref(bundle_id="b")).check_result.passed
    assert not resolver.resolve_support(
        ObjectRef("b", "active", "schema", "/payload/value"),
        require_object=True,
    ).check_result.passed


def test_ledger_trace_replays_event_payload_and_detects_tampering() -> None:
    ledger = ResidualLedger()
    residual = ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route")
    ledger.add(residual)
    ledger.events[0] = replace(ledger.events[0], post_state_digest="tampered")
    assert not ledger.trace_ok().passed

    redaction_ledger = ResidualLedger()
    redacted = ResidualRecord(ResidualKind.UNTRANSLATED, "o", ("s",), "redact")
    redaction_ledger.add(redacted)
    redaction, _ = redaction_ledger.redact(redacted.residual_id, reason="privacy")
    del redaction_ledger.residuals[redaction.residual_id]
    assert not redaction_ledger.trace_ok().passed


@pytest.mark.parametrize("route_type", list(ResidualMetabolismRoute))
def test_each_residual_metabolism_route_can_be_live(route_type: ResidualMetabolismRoute) -> None:
    deadline = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    residual = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "o",
        ("s",),
        "route",
        route=ResidualRoute(
            "owner",
            deadline,
            ("1h",),
            "daily",
            route_type=route_type,
        ),
    )

    assert check_residual_liveness(residual).passed


@pytest.mark.parametrize(
    "route",
    [
        ResidualRoute("", "2999-01-01T00:00:00Z", ("1h",), "daily"),
        ResidualRoute("owner", "2999-01-01T00:00:00Z", (), "daily"),
        ResidualRoute("owner", "2999-01-01T00:00:00Z", ("1h",), ""),
        ResidualRoute("owner", "", ("1h",), "daily"),
        ResidualRoute("owner", "not-a-date", ("1h",), "daily"),
        ResidualRoute(
            "owner",
            "2999-01-01T00:00:00Z",
            ("1h",),
            "daily",
            active_follow_through=False,
        ),
    ],
)
def test_residual_route_requires_live_follow_through(route: ResidualRoute) -> None:
    residual = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "o",
        ("s",),
        "route",
        route=route,
    )

    assert not check_residual_liveness(residual).passed


def test_frontier_and_aperture_comparisons_detect_packet_spam_and_debt() -> None:
    before_frontier = VerifiableFrontierProfile(
        [FrontierEntry("u", "transform", ("p1",), ("r1",), ("1h",))]
    )
    after_frontier = VerifiableFrontierProfile(
        [FrontierEntry("u", "transform", ("p1", "p2"), ("r1",), ("1h",))]
    )
    assert (
        before_frontier.compare(after_frontier, before_packet_count=1, after_packet_count=2)
        == FrontierComparison.PACKET_SPAM
    )
    expanded_frontier = VerifiableFrontierProfile(
        [
            FrontierEntry("u", "transform", ("p1",), ("r1",), ("1h",)),
            FrontierEntry("v", "transform", ("p2",), ("r2",), ("1h",)),
        ]
    )
    refined_frontier = VerifiableFrontierProfile(
        [FrontierEntry("u", "repair", ("p3",), ("r3",), ("1h",))]
    )
    regressed_frontier = VerifiableFrontierProfile(
        [FrontierEntry("z", "other", ("p4",), ("r4",), ("1h",))]
    )
    assert before_frontier.compare(before_frontier) == FrontierComparison.UNCHANGED
    assert before_frontier.compare(expanded_frontier) == FrontierComparison.EXPANDED
    assert before_frontier.compare(refined_frontier) == FrontierComparison.UNCHANGED
    assert before_frontier.compare(regressed_frontier) == FrontierComparison.REGRESSED
    assert expanded_frontier.compare(refined_frontier) == FrontierComparison.REFINED
    before_frontier.add(FrontierEntry("added", "manual", ("p5",), ("r5",), ("1h",)))
    assert len(before_frontier.entries) == 2

    before_aperture = Aperture(
        question_form_capacity=CapacityRecord("question", feasible_capacity=2)
    )
    after_aperture = Aperture(
        question_form_capacity=CapacityRecord(
            "question",
            feasible_capacity=1,
            residual_obligations=("aperture-debt",),
        )
    )
    assert before_aperture.compare(after_aperture) == ApertureComparison.NARROWED_WITH_RESIDUAL


def test_json_store_uses_stable_serde_and_atomic_save() -> None:
    source = inspect.getsource(json_store)
    assert "verification_ecology_kit.cli" not in source
    assert "ecology_state_from_json" in source
    assert "NamedTemporaryFile" in source
    assert "os.replace" in source


def test_json_store_rejects_symlink_targets(tmp_path: Path) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(ValueError, match="symlinked store path"):
        json_store._reject_symlink_target(link)

    real_dir = tmp_path / "real"
    real_dir.mkdir()
    dir_link = tmp_path / "dir-link"
    try:
        dir_link.symlink_to(real_dir, target_is_directory=True)
    except OSError:
        return
    with pytest.raises(ValueError, match="symlinked directory"):
        json_store._reject_symlink_target(dir_link / "state.json")
