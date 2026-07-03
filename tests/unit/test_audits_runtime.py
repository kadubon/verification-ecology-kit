from __future__ import annotations

from datetime import UTC, datetime, timedelta

from verification_ecology_kit.audit.adversarial_ingress import audit_adversarial_ingress
from verification_ecology_kit.audit.aperture_regression import audit_aperture_regression
from verification_ecology_kit.audit.packet_ecology import audit_packet_ecology
from verification_ecology_kit.audit.residual_metabolism import audit_residual_metabolism
from verification_ecology_kit.audit.schema_overclosure import audit_schema_overclosure
from verification_ecology_kit.model.aperture import Aperture, CapacityRecord
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import ResidualKind, TrustStatus, Visibility
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
    assert store.load().packet_population
