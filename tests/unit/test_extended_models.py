from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from verification_ecology_kit.audit.monoculture import audit_monoculture
from verification_ecology_kit.audit.reports import AuditEngine, AuditFinding, AuditReport
from verification_ecology_kit.audit.security import scan_secrets, verify_package_paths
from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.digest import Digest, DigestPolicy, check_record_digest
from verification_ecology_kit.errors import ErrorCode, VEKError
from verification_ecology_kit.ids import stable_id
from verification_ecology_kit.model.boundaries import BoundaryRecord
from verification_ecology_kit.model.circulation import ExternalPacket, LocalSovereignty
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.contracts import (
    CarrierContract,
    CheckerContract,
    ContractRegistry,
)
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.frontier import FrontierEntry, VerifiableFrontierProfile
from verification_ecology_kit.model.maturity import MaturityProfile
from verification_ecology_kit.model.overclosure import (
    OverclosureWitness,
    VerifierMonocultureDetector,
)
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.reachability import (
    CounterexampleChannel,
    ReachabilityCertificate,
)
from verification_ecology_kit.model.records import (
    ConformanceProfile,
    LifecycleStatus,
    ResidualKind,
)
from verification_ecology_kit.model.registries import (
    CarrierRegistry,
    CarrierRegistryEntry,
    CheckerRegistry,
    CheckerRegistryEntry,
)
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute, SoundGapResidual
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.references import (
    ObjectEnvelope,
    ObjectRef,
    ReferenceResolver,
    SchemaCatalogue,
)
from verification_ecology_kit.result import (
    CheckOutcome,
    CheckResult,
    ConformanceReport,
    FailureCode,
)
from verification_ecology_kit.runtime.json_store import JsonStore
from verification_ecology_kit.runtime.policies import DefaultRuntimePolicy


def test_boundary_registry_frontier_maturity_and_reports() -> None:
    assert not BoundaryRecord("b", "destructive").check().passed
    assert (
        BoundaryRecord("b", "destructive", reachability_certificate_refs=("cert",)).check().passed
    )

    carrier_registry = CarrierRegistry(
        {
            "active": CarrierRegistryEntry("active", "record", "d", "c", "checker", "1"),
            "migrated": CarrierRegistryEntry(
                "migrated",
                "record",
                "d",
                "c",
                "checker",
                "1",
                status=LifecycleStatus.MIGRATED,
                migration_witness_ref="wit",
            ),
            "stale": CarrierRegistryEntry(
                "stale", "record", "d", "c", "checker", "1", status=LifecycleStatus.STALE
            ),
        }
    )
    assert carrier_registry.accept("active").passed
    assert carrier_registry.accept("migrated").passed
    assert not carrier_registry.accept("missing").passed
    assert carrier_registry.accept("stale").result == CheckOutcome.RESIDUALIZE

    checker_registry = CheckerRegistry(
        {
            "active": CheckerRegistryEntry("active", "policy", "1"),
            "migrated": CheckerRegistryEntry(
                "migrated",
                "policy",
                "1",
                status=LifecycleStatus.MIGRATED,
                acceptance_judgment_ref="judgment",
            ),
        }
    )
    assert checker_registry.accept("active").passed
    assert checker_registry.accept("migrated").passed

    contracts = ContractRegistry()
    contracts.carrier_contracts["c"] = CarrierContract("c", "record", "d", "c", ("1",))
    contracts.checker_contracts["q"] = CheckerContract("q", "policy", ("1",))
    assert contracts.carrier_contracts["c"].migration_witness_required

    frontier = VerifiableFrontierProfile()
    frontier.add(FrontierEntry("u", "repair", ("p",), ("r",), ("1h",)))
    assert frontier.to_dict()["entries"]
    assert MaturityProfile(scalar_dashboard_label="local").to_dict()[
        "evidence_not_replaced_by_label"
    ]

    report = AuditReport("x", "pass", findings=[AuditFinding("c", "m")])
    assert "Report digest" in report.to_markdown()
    engine = AuditEngine()
    assert engine.packet_ecology([VerifierPacket.minimal()]).decision == "residualize"


def test_reachability_and_soundgap_paths() -> None:
    channel = CounterexampleChannel(
        "ch",
        "target",
        cex_closed_result="closed_within_window",
    )
    cert = ReachabilityCertificate(
        certificate_id="cert",
        object_id="obj",
        schema_version="1",
        canonical_digest=Digest("sha256", "abc"),
        status=LifecycleStatus.ACTIVE,
        predicate="destructive",
        certificate_contract="contract",
        carrier_id="carrier",
        carrier_acceptance_judgment_ref="j-carrier",
        carrier_type="empty",
        concretization_id="conc",
        checker_id="checker",
        checker_acceptance_judgment_ref="j-checker",
        checker_result="pass",
        claim_kind="exclusion",
        coverage_statement="covered",
        cover_check_result="pass",
        empty_concretization_statement="empty",
        empty_check_result="pass",
        cex_channel=channel,
        soundness_target="empty reachability",
    )
    assert cert.admissible_exclusion().passed

    stale = cert
    stale.status = LifecycleStatus.STALE
    assert not stale.admissible_exclusion().passed

    deadline = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    gap = SoundGapResidual.create(
        certificate_ref="cert",
        gap_kind="expired_budget",
        semantic_target="target",
        operational_claim="claim",
        route=ResidualRoute("owner", deadline, ("1h",), "daily"),
    )
    cert.status = LifecycleStatus.ACTIVE
    cert.soundgap_residuals = (gap,)
    assert not cert.admissible_exclusion().passed


def test_circulation_operations_json_store_and_policy(tmp_path: Path) -> None:
    packet = VerifierPacket.from_external_candidate()
    sovereignty = LocalSovereignty()
    assert sovereignty.quarantine_external(ExternalPacket(packet, "source", "clock")).passed
    assert not sovereignty.internalize(packet, translated=False, boundary_checked=True).internalized
    packet.counter_packet_refs.append("counter")
    packet.circulation_status.translation_residual_refs.append("translation-residual")
    assert sovereignty.internalize(
        packet,
        translated=True,
        boundary_checked=True,
        residuals_handled=True,
        local_counter_packet_hook=True,
    ).internalized

    engine = PacketOperationEngine()
    packet = VerifierPacket.minimal()
    assert engine.fork(packet).output_packet is not None
    assert engine.specialize(packet, scope="scope").output_packet is not None
    assert engine.generalize(packet).residual_refs
    assert engine.contrast(packet, VerifierPacket.minimal()).output_packet is not None
    assert engine.repair(packet, repair_note="fix").output_packet is not None
    assert engine.retire(packet, reason="done").output_packet is not None
    assert engine.quarantine(packet, reason="test").output_packet is not None

    assert DefaultRuntimePolicy().should_quarantine(VerifierPacket.minimal())
    store_path = tmp_path / "state.json"
    store = JsonStore(store_path)
    state = VerifierEcologyState()
    state.add_packet(packet)
    store.save(state)
    loaded = store.load()
    assert packet.packet_id in loaded.packet_population
    assert loaded.history.events


def test_conformance_failure_branches_and_references() -> None:
    envelope = ObjectEnvelope("o", "schema", "1.0", {"value": "x"})
    envelope.refresh_digest()
    catalogue = SchemaCatalogue("cat", {"schema": ("1.0",)}, {"schema": {"type": "object"}})
    bundle = VetBundle("b", "1", ConformanceProfile.CORE, catalogue, [envelope])
    assert ConformanceEngine().run(bundle).decision.value == "accept"

    bad_digest = ObjectEnvelope("bad", "schema", "1.0", {"value": "x"}, Digest("sha256", "bad"))
    bad_bundle = VetBundle("b", "1", ConformanceProfile.CORE, catalogue, [bad_digest])
    assert ConformanceEngine().run(bad_bundle).decision.value == "reject"

    residual = ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route")
    bad_bundle = VetBundle("b", "1", ConformanceProfile.CORE, catalogue, [envelope])
    bad_bundle.residual_ledger.add(residual)
    assert ConformanceEngine().run(bad_bundle).decision.value == "accept_with_residuals"

    ref = ObjectRef("other", "o", "schema", digest=envelope.canonical_digest)
    _, _, result = ReferenceResolver(bundle_id="b", envelopes=[envelope]).resolve(ref)
    assert not result.passed

    with pytest.raises(VEKError) as exc:
        DigestPolicy().hash_bytes(b"x", algorithm_id="md5")
    assert exc.value.code == ErrorCode.UNSUPPORTED_DIGEST_ALGORITHM
    assert check_record_digest({"a": 1}, DigestPolicy().digest_json({"a": 1})).passed


def test_misc_detectors_and_json_branches(tmp_path: Path) -> None:
    assert stable_id("x", {"a": 1}).startswith("x_")
    assert not OverclosureWitness("w", (), ("scope",), ("regression",), (), (), ()).is_overclosing()
    assert OverclosureWitness("w", ("gain",), ("scope",), ("regression",), (), (), ()).to_dict()
    assert (
        VerifierMonocultureDetector()
        .detect(
            origin_assumptions=[("a",), ("b",)],
            question_forms=[("q1",), ("q2",)],
            residual_filters=[("r1",), ("r2",)],
            counter_packet_routes=[("c1",), ("c2",)],
        )
        .passed
    )
    assert (
        audit_monoculture(
            origin_assumptions=[("same",), ("same",)],
            question_forms=[("q",), ("q",)],
            residual_filters=[("r",), ("r",)],
            counter_packet_routes=[(), ()],
        ).decision
        == "residualize"
    )

    with pytest.raises(VEKError):
        Canonicalizer().canonicalize({1: "bad"})
    with pytest.raises(VEKError):
        Canonicalizer().canonicalize(object())

    private_key = tmp_path / "key.txt"
    private_key.write_text("BEGIN " + "PRIVATE KEY", encoding="utf-8")
    assert scan_secrets(tmp_path).decision == "quarantine"
    env_file = tmp_path / ".env"
    env_file.write_text("A=B", encoding="utf-8")
    assert scan_secrets(tmp_path).decision == "quarantine"
    assert verify_package_paths([Path(".ipynb_checkpoints/check")]).decision == "quarantine"


def test_report_decision_helpers() -> None:
    report = ConformanceReport.from_results(
        profile="core",
        ordered_check_results=[
            CheckResult(
                "Security",
                CheckOutcome.FAIL,
                failure_codes=(FailureCode.SECRET_LEAK,),
            )
        ],
    )
    assert report.decision.value == "quarantine"
    report = ConformanceReport.from_results(
        profile="core",
        ordered_check_results=[
            CheckResult(
                "AuthorityOK",
                CheckOutcome.FAIL,
                failure_codes=(FailureCode.AUTHORITY_MISMATCH,),
            )
        ],
    )
    assert report.decision.value == "reject"


def test_operation_wrapper_and_port_imports() -> None:
    import verification_ecology_kit.operations.compose
    import verification_ecology_kit.operations.contrast
    import verification_ecology_kit.operations.fork
    import verification_ecology_kit.operations.generalize
    import verification_ecology_kit.operations.internalize
    import verification_ecology_kit.operations.quarantine
    import verification_ecology_kit.operations.redact
    import verification_ecology_kit.operations.repair
    import verification_ecology_kit.operations.retire
    import verification_ecology_kit.operations.specialize
    import verification_ecology_kit.ports.checker
    import verification_ecology_kit.ports.clock
    import verification_ecology_kit.ports.reporter

    assert verification_ecology_kit.operations.compose.PacketOperationEngine
    packet = VerifierPacket.minimal()
    assert verification_ecology_kit.operations.fork.fork(packet).operation.value == "fork"
    assert (
        verification_ecology_kit.operations.specialize.specialize(
            packet, scope="unit"
        ).operation.value
        == "specialize"
    )
    assert (
        verification_ecology_kit.operations.generalize.generalize(packet).operation.value
        == "generalize"
    )
    assert (
        verification_ecology_kit.operations.compose.compose(
            packet, VerifierPacket.minimal()
        ).operation.value
        == "compose"
    )
    assert (
        verification_ecology_kit.operations.contrast.contrast(
            packet, VerifierPacket.minimal()
        ).operation.value
        == "contrast"
    )
    assert (
        verification_ecology_kit.operations.repair.repair(
            packet, repair_note="unit"
        ).operation.value
        == "repair"
    )
    assert (
        verification_ecology_kit.operations.retire.retire(packet, reason="unit").operation.value
        == "retire"
    )
    assert (
        verification_ecology_kit.operations.quarantine.quarantine(
            packet, reason="unit"
        ).operation.value
        == "quarantine"
    )
    assert (
        verification_ecology_kit.operations.internalize.internalize(
            packet,
            translated=True,
            boundary_checked=True,
        ).operation.value
        == "internalize"
    )
    assert (
        verification_ecology_kit.operations.redact.redact(packet, fields=("local",)).operation.value
        == "redact"
    )
