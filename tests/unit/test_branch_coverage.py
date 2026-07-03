from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from verification_ecology_kit.audit.aperture_regression import audit_aperture_regression
from verification_ecology_kit.audit.local_info import scan_local_info
from verification_ecology_kit.audit.reports import AuditEngine
from verification_ecology_kit.audit.residual_metabolism import audit_residual_metabolism
from verification_ecology_kit.audit.security import verify_package_paths
from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.cli import main
from verification_ecology_kit.digest import Digest, DigestPolicy, check_record_digest
from verification_ecology_kit.errors import ErrorCode, VEKError
from verification_ecology_kit.model.aperture import Aperture, CapacityRecord
from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.contracts import JudgmentContract
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.judgments import JudgmentRecord, UseContext, jvalid
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.packets import CirculationStatus, VerifierPacket
from verification_ecology_kit.model.reachability import CounterexampleChannel
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    ConformanceProfile,
    LifecycleStatus,
    ResidualKind,
    TrustStatus,
    Visibility,
)
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.references import (
    ObjectEnvelope,
    ObjectRef,
    ReferenceResolver,
    SchemaCatalogue,
    resolve_pointer,
)
from verification_ecology_kit.runtime.json_store import JsonStore
from verification_ecology_kit.runtime.policies import DefaultRuntimePolicy


def test_cli_exception_and_markdown_output(tmp_path: Path, capsys) -> None:
    assert main(["digest", str(tmp_path / "missing.json")]) == 2
    assert json.loads(capsys.readouterr().err)["error"]

    bundle = tmp_path / "bundle.json"
    bundle.write_text(
        json.dumps({"bundle_id": "b", "schema_version": "1", "objects": []}),
        encoding="utf-8",
    )
    assert main(["conformance", str(bundle), "--format", "markdown"]) == 0
    assert "Decision" in capsys.readouterr().out


def test_audit_branch_paths(tmp_path: Path) -> None:
    engine = AuditEngine()
    state = VerifierEcologyState()
    residual = ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route")
    state.residual_ledger.add(residual)
    assert engine.residual_metabolism(state).decision == "residualize"
    state.residual_ledger.retire(residual.residual_id, justification="done")
    assert audit_residual_metabolism(state).decision == "pass"

    before = Aperture(question_form_capacity=CapacityRecord("question", feasible_capacity=2))
    after = Aperture(
        question_form_capacity=CapacityRecord(
            "question",
            feasible_capacity=1,
            residual_obligations=("aperture-debt",),
        )
    )
    assert engine.aperture_regression(before, after).decision == "residualize"
    assert audit_aperture_regression(after, before).decision == "pass"

    local = tmp_path / "local.txt"
    local.write_text("C:" + "\\Users\\allowed\\file.txt", encoding="utf-8")
    assert scan_local_info(local, allowlist=("allowed",)).decision == "pass"
    assert verify_package_paths([]).decision == "pass"


def test_canonical_reference_and_digest_failure_branches() -> None:
    canonicalizer = Canonicalizer()
    with pytest.raises(VEKError):
        canonicalizer.prepare(Decimal("1.234567890123456789"))
    with pytest.raises(VEKError):
        canonicalizer.prepare(float("nan"))
    assert canonicalizer.loads('{"n": 1.5}')["n"] == 1.5

    with pytest.raises(VEKError):
        resolve_pointer({"a": 1}, "a")
    with pytest.raises(VEKError):
        resolve_pointer({"a": []}, "/a/x")
    with pytest.raises(VEKError):
        resolve_pointer({"a": []}, "/a/1")
    with pytest.raises(VEKError):
        resolve_pointer({"a": 1}, "/a/b")

    envelope = ObjectEnvelope("o", "schema", "1", {"x": 1})
    envelope.refresh_digest()
    resolver = ReferenceResolver(bundle_id="b", envelopes=[envelope])
    assert not resolver.resolve(ObjectRef("b", "missing", "schema"))[2].passed
    assert not resolver.resolve(ObjectRef("b", "o", "other"))[2].passed
    assert not resolver.resolve(ObjectRef("b", "o", "schema", pointer="/missing"))[2].passed

    assert not check_record_digest({"a": 2}, DigestPolicy().digest_json({"a": 1})).passed


def test_conformance_failure_branches() -> None:
    envelope = ObjectEnvelope("o", "schema", "1", {"x": 1})
    envelope.refresh_digest()
    catalogue = SchemaCatalogue(
        "cat",
        {"schema": ("1",)},
        {"schema": {"type": "object", "required": ["missing"]}},
    )
    bundle = VetBundle("b", "1", ConformanceProfile.CORE, catalogue, [envelope])
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    envelope = ObjectEnvelope("o", "schema", "1", {"x": 1}, Digest("md5", "bad"))
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.CORE,
        SchemaCatalogue("cat", {"schema": ("1",)}),
        [envelope],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    good = ObjectEnvelope("o", "schema", "1", {"x": 1})
    good.refresh_digest()
    duplicate = ObjectEnvelope("o", "schema", "1", {"x": 2})
    duplicate.refresh_digest()
    bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.CORE,
        SchemaCatalogue("cat", {"schema": ("1",)}),
        [good, duplicate],
    )
    assert ConformanceEngine().run(bundle).decision.value == "reject"

    op = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1",)}),
        [good],
        authority_decisions=[{"decision": "allow", "decision_status": "stale"}],
        judgment_records=[{"JValid_result": "fail"}],
    )
    assert ConformanceEngine().run(op).decision.value == "reject"


def test_authority_judgment_runtime_and_ledger_branches(tmp_path: Path) -> None:
    decision = AuthorityDecision(
        "a",
        "obj",
        "1",
        Digest("sha256", "abc"),
        LifecycleStatus.ACTIVE,
        "policy",
        AuthorityAction.DEPLOYMENT,
        AuthorityDecisionValue.RESIDUALIZE,
        residual_gates=("gate",),
    )
    value, result = AuthorityEngine().aggregate(AuthorityAction.DEPLOYMENT, [decision])
    assert value == AuthorityDecisionValue.RESIDUALIZE
    assert result.result.value == "residualize"

    allow = AuthorityDecision(
        "a2",
        "obj",
        "1",
        Digest("sha256", "abc"),
        LifecycleStatus.ACTIVE,
        "policy",
        AuthorityAction.DEPLOYMENT,
        AuthorityDecisionValue.ALLOW,
        sandbox_required=True,
        sandbox_status="failed",
    )
    assert (
        AuthorityEngine().aggregate(AuthorityAction.DEPLOYMENT, [allow])[0]
        == AuthorityDecisionValue.DENY
    )

    ref = ObjectRef("b", "obj", "schema", digest=Digest("sha256", "abc"))
    context = UseContext(
        ref,
        "",
        ref,
        (),
        "act",
        "ledger",
        "policy",
        "1",
        "sha256",
        ref,
        Digest("sha256", "abc"),
        "fresh",
        (),
        "clock",
    )
    record = JudgmentRecord(
        "j",
        "kind",
        ref,
        "checker",
        "1",
        "1",
        "j",
        Digest("sha256", "abc"),
        "u",
        ref,
        "",
        Digest("sha256", "different"),
        "sha256",
        "pass",
    )
    assert not jvalid(record, context, JudgmentContract("kind", "s", "d", "c", "r")).passed

    ledger = ResidualLedger()
    target = ResidualRecord(ResidualKind.CONFLICT_RESIDUAL, "o", ("s",), "missing merge")
    ledger.merge(("missing",), target)
    assert target.kind == ResidualKind.CONFLICT_RESIDUAL

    policy = DefaultRuntimePolicy(require_boundary_refs=False)
    packet = VerifierPacket.minimal()
    assert not policy.should_quarantine(packet)
    packet.circulation_status = CirculationStatus(visibility=Visibility.REDACTED)
    assert policy.should_quarantine(packet)
    packet.circulation_status = CirculationStatus(trust_status=TrustStatus.LOW_TRUST)
    assert policy.should_quarantine(packet)

    assert "json_store_snapshot" not in JsonStore(tmp_path / "missing.json").load().archive
    raw_store = tmp_path / "raw-state.json"
    raw_store.write_text('["legacy"]', encoding="utf-8")
    assert JsonStore(raw_store).load().archive["json_store_snapshot"] == ["legacy"]


def test_counterexample_channel_branches_and_error_to_dict() -> None:
    assert not CounterexampleChannel("c", "t", status=LifecycleStatus.STALE).cex_closed().passed
    assert not CounterexampleChannel("c", "t", unresolved_reports=("r",)).cex_closed().passed
    assert (
        CounterexampleChannel("c", "t", cex_closed_result="unknown").cex_closed().result.value
        == "residualize"
    )
    err = VEKError(ErrorCode.POLICY_VIOLATION, "policy")
    assert err.to_dict()["code"] == "policy_violation"
