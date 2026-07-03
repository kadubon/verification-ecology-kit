from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.ledger import TraceCertificate
from verification_ecology_kit.model.overclosure import OverclosureWitness
from verification_ecology_kit.model.packets import BoundaryTesterPacket, VerifierPacket
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    ConformanceProfile,
    LifecycleStatus,
)
from verification_ecology_kit.model.registries import CheckerRegistry, CheckerRegistryEntry
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.references import (
    DigestRecord,
    ObjectEnvelope,
    ObjectRef,
    ReferenceResolver,
    SchemaCatalogue,
    SchemaMigrationWitness,
)
from verification_ecology_kit.runtime.engine import RuntimeEngine
from verification_ecology_kit.runtime.in_memory import InMemoryStore

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "golden"
FIXTURES = ROOT / "fixtures"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bundle_from_case(data: dict[str, Any]) -> VetBundle:
    bundle_data = data["bundle"]
    objects: list[ObjectEnvelope] = []
    for item in bundle_data.get("objects", []):
        digest = item.get("canonical_digest", {"algorithm_id": "sha256", "value": ""})
        objects.append(
            ObjectEnvelope(
                item["object_id"],
                item["schema_id"],
                item["schema_version"],
                item.get("payload", {}),
                canonical_digest=Digest(digest["algorithm_id"], digest["value"]),
            )
        )
    accepted = {
        schema_id: tuple({obj.schema_version for obj in objects if obj.schema_id == schema_id})
        for schema_id in {obj.schema_id for obj in objects}
    }
    if not accepted:
        accepted = {"verifier-packet": ("1.0",)}
    return VetBundle(
        str(bundle_data["bundle_id"]),
        str(bundle_data["schema_version"]),
        ConformanceProfile(str(bundle_data["conformance_profile"])),
        SchemaCatalogue("golden", accepted),
        objects,
    )


def test_fixture_directories_are_non_empty() -> None:
    assert list(FIXTURES.glob("*.json"))
    assert len(list(GOLDEN.glob("*.json"))) >= 10


def test_theory_coverage_fixture_has_no_v1_gaps() -> None:
    data = _load(GOLDEN / "theory_coverage.expected.json")
    terms = data["terms"]
    assert len(terms) >= 50
    for item in terms:
        assert item["status"] in {"implemented", "not_applicable"}
        assert item["schema"]
        assert (ROOT.parent / item["docs"]).is_file()
        for test_path in item["tests"]:
            assert (ROOT.parent / test_path).is_file()


def test_golden_conformance_cases() -> None:
    for path in [GOLDEN / "minimal_core_bundle.json", GOLDEN / "invalid_digest.json"]:
        data = _load(path)
        report = ConformanceEngine().run(_bundle_from_case(data))
        assert report.decision.value == data["expected_decision"]


def test_golden_reference_registry_and_packet_cases() -> None:
    ref_case = _load(GOLDEN / "unresolved_reference.json")
    envelope = ObjectEnvelope(
        ref_case["object_id"],
        "example-object",
        "1.0",
        {"value": "x"},
    )
    envelope.refresh_digest()
    ref = ObjectRef(ref_case["bundle_id"], ref_case["missing_object_id"], "example-object")
    _, _, result = ReferenceResolver(bundle_id=ref_case["bundle_id"], envelopes=[envelope]).resolve(
        ref
    )
    assert result.result.value == ref_case["expected_result"]
    assert result.failure_codes[0].value == ref_case["expected_failure"]

    checker_case = _load(GOLDEN / "stale_checker.json")
    registry = CheckerRegistry(
        {
            checker_case["checker_id"]: CheckerRegistryEntry(
                checker_case["checker_id"],
                "policy",
                "1",
                status=LifecycleStatus(checker_case["status"]),
            )
        }
    )
    assert (
        registry.accept(checker_case["checker_id"]).result.value == checker_case["expected_result"]
    )

    packet_case = _load(GOLDEN / "missing_counter_packet_residual.json")
    packet_result = {result.check_name: result for result in VerifierPacket.minimal().validate()}[
        packet_case["expected_check"]
    ]
    assert packet_result.result.value == packet_case["expected_result"]
    assert packet_result.failure_codes[0].value == packet_case["expected_failure"]


def test_golden_operation_authority_runtime_and_counter_cases() -> None:
    external = VerifierPacket.from_external_candidate()
    external_case = _load(GOLDEN / "external_packet_quarantine.json")
    assert external.circulation_status is not None
    assert external.circulation_status.visibility.value == external_case["expected_visibility"]
    assert external.circulation_status.trust_status.value == external_case["expected_trust_status"]

    overclosure_case = _load(GOLDEN / "overclosure_witness.json")
    witness = OverclosureWitness(
        overclosure_case["case_id"],
        tuple(overclosure_case["gain_record"]),
        tuple(overclosure_case["scope_and_measurement_context"]),
        tuple(overclosure_case["regression_records"]),
        (),
        tuple(overclosure_case["residual_adequacy_record"]),
        (),
    )
    assert witness.is_overclosing() is overclosure_case["expected_overclosing"]

    operation_case = _load(GOLDEN / "schema_overclosure_residual.json")
    packet = VerifierPacket.minimal()
    packet.extension.update(operation_case["extension"])
    report = PacketOperationEngine().repair(packet, repair_note="golden")
    assert report.schema_overclosure_risk.check_name == operation_case["expected_check"]
    assert report.schema_overclosure_risk.result.value == operation_case["expected_result"]

    authority_case = _load(GOLDEN / "authority_denial_due_to_stale_support.json")
    decision = AuthorityDecision(
        "auth-allow",
        "obj",
        "1",
        Digest("sha256", "abc"),
        LifecycleStatus.ACTIVE,
        "policy",
        AuthorityAction.DEPLOYMENT,
        AuthorityDecisionValue.ALLOW,
        required_support_refs=("support-active",),
    )
    value, auth_result = AuthorityEngine().aggregate(
        AuthorityAction.DEPLOYMENT,
        [decision],
        stale_or_unknown_support_refs=tuple(authority_case["stale_or_unknown_support_refs"]),
    )
    assert value.value == authority_case["expected_decision"]
    assert auth_result.result.value == authority_case["expected_result"]

    runtime_case = _load(GOLDEN / "runtime_history_residual.json")
    store = InMemoryStore()
    event = store.load().history.append(runtime_case["history_event_type"], {"detail": "golden"})
    engine = RuntimeEngine(store=store)
    engine.run_once()
    engine.run_once()
    matching = [
        residual
        for residual in store.load().residual_ledger.residuals.values()
        if residual.origin == event.event_id
    ]
    assert len(matching) == runtime_case["expected_residual_count_after_two_runs"]

    counter_case = _load(GOLDEN / "counter_packet_boundary_gap.json")
    target = VerifierPacket.minimal()
    target.boundary_refs = None
    counter = BoundaryTesterPacket.minimal()
    findings = counter.inspect_target(target)
    assert any(
        finding.issue == counter_case["expected_issue"]
        and finding.residual_kind.value == counter_case["expected_residual_kind"]
        for finding in findings
    )


def test_theory_record_serialization_witnesses() -> None:
    envelope = ObjectEnvelope("obj", "example-object", "1.0", {"value": "x"})
    digest = envelope.refresh_digest()
    ref = envelope.ref(bundle_id="b")
    digest_record = DigestRecord(
        "dig-1",
        ref,
        "1.0",
        "jcs-compatible",
        "sha256-default",
        "sha256",
        digest,
        object_digest_ok_judgment_ref="judgment-1",
    )
    assert digest_record.to_dict()["canonical_digest"]["value"] == digest.value

    witness = SchemaMigrationWitness(
        "mig-1",
        "1.0",
        "1.1",
        ref,
        ref,
        digest,
        Digest("sha256", "changed"),
        ("res-loss",),
        "judgment-migration",
    )
    assert witness.preserves_or_residualizes_loss()
    assert witness.to_dict()["loss_residual_refs"] == ["res-loss"]

    assert not TraceCertificate("trace-1", "partial").is_accepted_witness()
    assert TraceCertificate(
        "trace-2",
        "partial",
        representative_linearization_refs=("lin-1",),
    ).is_accepted_witness()
