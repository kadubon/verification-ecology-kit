from __future__ import annotations

from datetime import UTC, datetime, timedelta

from verification_ecology_kit.audit.adversarial_ingress import audit_adversarial_ingress
from verification_ecology_kit.audit.aperture_regression import audit_aperture_regression
from verification_ecology_kit.audit.packet_ecology import audit_packet_ecology
from verification_ecology_kit.audit.residual_metabolism import audit_residual_metabolism
from verification_ecology_kit.audit.schema_overclosure import audit_schema_overclosure
from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.aperture import Aperture, CapacityRecord
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.reachability import (
    CounterexampleChannel,
    ReachabilityCertificate,
)
from verification_ecology_kit.model.records import (
    LifecycleStatus,
    ResidualKind,
    TrustStatus,
    Visibility,
)
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute
from verification_ecology_kit.runtime.engine import RuntimeEngine
from verification_ecology_kit.runtime.in_memory import InMemoryStore


def test_packet_ecology_audit_residualizes_missing_counter() -> None:
    report = audit_packet_ecology([VerifierPacket.minimal()])
    assert report.decision == "residualize"


def test_residual_metabolism_audit_routes_live_residual() -> None:
    state = VerifierEcologyState()
    deadline = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    residual = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "o",
        ("s",),
        "inspect",
        route=ResidualRoute("owner", deadline, ("1h",), "daily"),
    )
    state.residual_ledger.add(residual)
    report = audit_residual_metabolism(state)
    assert report.decision == "pass"


def test_aperture_regression_rejects_silent_loss() -> None:
    before = Aperture(question_form_capacity=CapacityRecord("question", feasible_capacity=2))
    after = Aperture(question_form_capacity=CapacityRecord("question", feasible_capacity=1))
    report = audit_aperture_regression(before, after)
    assert report.decision == "reject"


def test_schema_overclosure_audit_creates_finding() -> None:
    report = audit_schema_overclosure(schema_rejected_unknown=True)
    assert report.decision == "residualize"


def test_adversarial_ingress_requires_quarantine() -> None:
    packet = VerifierPacket.minimal()
    packet.circulation_status.trust_status = TrustStatus.ADVERSARIAL
    packet.circulation_status.visibility = Visibility.PUBLIC
    report = audit_adversarial_ingress(packet)
    assert report.decision == "quarantine"


def test_runtime_generates_packet_from_residual() -> None:
    store = InMemoryStore()
    state = store.load()
    residual = ResidualRecord(ResidualKind.UNRESOLVED, "history", ("unknown",), "generate")
    state.residual_ledger.add(residual)
    report = RuntimeEngine(store=store).run_once()
    assert report.generated_packets
    assert report.generated_from_residuals
    assert report.frontier_updates
    assert report.aperture_updates
    assert report.counter_packet_obligations
    assert report.schema_checks
    assert report.stages
    assert all(isinstance(item, dict) for item in report.reachability_checks)
    assert store.load().packet_population


class _ReachableGenerator:
    def from_residual(self, residual: ResidualRecord) -> list[VerifierPacket]:
        packet = VerifierPacket.minimal()
        assert packet.boundary_refs is not None
        assert packet.anti_overclosure is not None
        assert packet.update_profile is not None
        packet.boundary_refs.reachability_certificate_refs.append("reach-1")
        packet.anti_overclosure.unknowns_to_preserve.append("unknown")
        packet.anti_overclosure.lineage_laundering_checks.append("lineage")
        packet.update_profile.retirement_conditions.append("manual")
        packet.counter_packet_refs.append("counter")
        return [packet]


def test_runtime_calls_reachability_certificate_material() -> None:
    store = InMemoryStore()
    state = store.load()
    state.residual_ledger.add(ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route"))
    certificate = ReachabilityCertificate(
        certificate_id="reach-1",
        object_id="packet",
        schema_version="1.0",
        canonical_digest=Digest("sha256", "abc"),
        status=LifecycleStatus.ACTIVE,
        predicate="destructive",
        certificate_contract="absence-v1",
        carrier_id="carrier",
        carrier_acceptance_judgment_ref="carrier-ok",
        carrier_type="proof_object",
        concretization_id="concrete",
        checker_id="checker",
        checker_acceptance_judgment_ref="checker-ok",
        checker_result="pass",
        claim_kind="exclusion",
        coverage_statement="covered",
        cover_check_result="pass",
        empty_concretization_statement="empty",
        empty_check_result="pass",
        cex_channel=CounterexampleChannel(
            "cex",
            "packet",
            cex_closed_result="closed_within_window",
        ),
        soundness_target="absence",
    )
    state.archive["reachability_certificates"] = {"reach-1": certificate.to_dict()}

    report = RuntimeEngine(store=store, generator=_ReachableGenerator()).run_once()

    assert report.reachability_checks[0]["result"] == "pass"


def test_runtime_reachability_and_schema_negative_helpers() -> None:
    engine = RuntimeEngine()
    state = VerifierEcologyState()
    packet = VerifierPacket.minimal()
    assert packet.boundary_refs is not None
    packet.boundary_refs.reachability_certificate_refs.append("missing")

    missing = engine._reachability_result(packet, state)
    assert missing.result.value == "residualize"

    bad_certificate = ReachabilityCertificate(
        certificate_id="bad",
        object_id="packet",
        schema_version="1.0",
        canonical_digest=Digest("sha256", "abc"),
        status=LifecycleStatus.STALE,
        predicate="destructive",
        certificate_contract="absence-v1",
        carrier_id="carrier",
        carrier_acceptance_judgment_ref="carrier-ok",
        carrier_type="proof_object",
        concretization_id="concrete",
        checker_id="checker",
        checker_acceptance_judgment_ref="checker-ok",
        checker_result="pass",
        claim_kind="exclusion",
        coverage_statement="covered",
        cover_check_result="pass",
        empty_concretization_statement="empty",
        empty_check_result="pass",
        cex_channel=CounterexampleChannel(
            "cex",
            "packet",
            cex_closed_result="closed_within_window",
        ),
        soundness_target="absence",
    )
    packet.boundary_refs.reachability_certificate_refs = ["bad", "unknown-type"]
    state.archive["reachability_certificates"] = {"bad": bad_certificate, "unknown-type": object()}
    blocked = engine._reachability_result(packet, state)
    assert blocked.result.value == "fail"
    assert engine._reachability_certificate(state, "unknown-type") is None

    core_residual = ResidualRecord(ResidualKind.MISSING, "packet", ("core",), "fill")
    schema = engine._schema_overclosure_result(packet, created_core=[core_residual], state=state)
    assert schema.result.value == "residualize"
