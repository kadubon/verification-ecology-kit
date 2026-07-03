from __future__ import annotations

from verification_ecology_kit.model.packets import CounterPacket, VerifierPacket
from verification_ecology_kit.model.records import ResidualKind, Visibility
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.result import CheckOutcome


def test_minimal_packet_is_core_complete_but_missing_counter_and_boundaries() -> None:
    packet = VerifierPacket.minimal()
    results = packet.validate()
    assert not packet.missing_core_fields()
    assert any(result.check_name == "CounterPacketAdequacy" for result in results)
    assert any(result.check_name == "PacketSemanticAccountability" for result in results)


def test_missing_core_is_residualized() -> None:
    packet = VerifierPacket(
        origin=None,
        scope=None,
        transformation_class=None,
        verifier_procedure=None,
        certification_condition=None,
        boundary_refs=None,
        residual_hooks=None,
        update_profile=None,
        circulation_status=None,
    )
    results = packet.validate()
    assert packet.missing_core_fields()
    assert packet.residual_obligations
    assert any(not result.passed for result in results)


def test_compose_requires_own_boundary_check() -> None:
    engine = PacketOperationEngine()
    left = VerifierPacket.minimal()
    right = VerifierPacket.minimal()
    right.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, right.packet_id, ("right",), "preserve")
    )
    report = engine.compose(left, right)
    assert report.output_packet is not None
    assert not report.boundary_safety.passed
    assert report.admissibility.result == CheckOutcome.FAIL
    assert {residual.residual_id for residual in right.residual_obligations}.issubset(
        {residual.residual_id for residual in report.output_packet.residual_obligations}
    )
    assert report.residual_refs


def test_internalize_without_translation_quarantines() -> None:
    engine = PacketOperationEngine()
    packet = VerifierPacket.from_external_candidate()
    report = engine.internalize(packet, translated=False, boundary_checked=False)
    assert report.output_packet is not None
    assert report.output_packet.circulation_status.visibility == Visibility.QUARANTINED
    assert report.admissibility.result == CheckOutcome.FAIL


def test_internalize_external_requires_quarantine_translation_record() -> None:
    engine = PacketOperationEngine()
    packet = VerifierPacket.from_external_candidate()
    report = engine.internalize(packet, translated=True, boundary_checked=True)
    assert report.output_packet is not None
    assert report.output_packet.circulation_status.visibility == Visibility.QUARANTINED
    assert report.output_packet.circulation_status.translation_residual_refs


def test_redact_preserves_redaction_residual() -> None:
    engine = PacketOperationEngine()
    packet = VerifierPacket.minimal()
    packet.extension["redacted_field"] = "field-value"
    report = engine.redact(packet, fields=("redacted_field",))
    assert report.output_packet is not None
    assert "redacted_field" not in report.output_packet.extension
    assert report.residual_refs


def test_counter_packet_finds_semantic_erasure_cases() -> None:
    target = VerifierPacket.from_external_candidate()
    target.origin.parent_packets.append("parent")
    target.anti_overclosure.future_candidates_may_narrow = True
    findings = CounterPacket.minimal().inspect_target(target)
    issues = {finding.residual_kind for finding in findings}
    assert ResidualKind.SCHEMA_OVERCLOSURE in issues
    assert ResidualKind.TRANSLATION_RESIDUAL in issues
    assert ResidualKind.APERTURE_DEBT in issues
