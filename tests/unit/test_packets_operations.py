from __future__ import annotations

from verification_ecology_kit.model.packets import BoundaryRefs, CounterPacket, VerifierPacket
from verification_ecology_kit.model.records import ResidualKind, Visibility
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.operations.base import PacketOperationEngine, PacketOperationName
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
    assert report.ecological_invariants.passed


def test_ecological_invariant_check_detects_dropped_counter_route() -> None:
    engine = PacketOperationEngine()
    parent = VerifierPacket.minimal()
    parent.counter_packet_refs.append("counter-parent")
    child = VerifierPacket.minimal()
    child.packet_id = "child"

    result = engine._check_ecological_invariants((parent,), child, boundary_checked=True)

    assert not result.passed


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


def test_packet_operations_cover_parent_context_and_success_paths() -> None:
    engine = PacketOperationEngine()
    parent = VerifierPacket.minimal()
    parent.origin = None
    parent.boundary_refs = BoundaryRefs(destructive_boundary_ref="boundary")
    parent.counter_packet_refs.append("counter")

    forked = engine.fork(parent)
    specialized = engine.specialize(parent, scope="new-scope")
    generalized = engine.generalize(parent, residualize_scope_loss=False)

    assert forked.output_packet is not None
    assert forked.output_packet.origin is not None
    assert specialized.output_packet is not None
    assert specialized.output_packet.scope is not None
    assert "new-scope" in specialized.output_packet.scope.applies_to
    assert generalized.boundary_safety.passed

    external = VerifierPacket.from_external_candidate()
    external.counter_packet_refs.append("counter")
    external.circulation_status.translation_residual_refs.append("translation-residual")
    internalized = engine.internalize(external, translated=True, boundary_checked=True)
    assert internalized.output_packet is not None
    assert internalized.output_packet.circulation_status.visibility == Visibility.PRIVATE


def test_packet_operations_cover_loss_and_none_branches() -> None:
    engine = PacketOperationEngine()
    packet = VerifierPacket.minimal()
    packet.circulation_status = None
    assert engine.retire(packet, reason="done").output_packet is not None
    assert engine.quarantine(packet, reason="hold").output_packet is not None

    packet.update_profile = None
    repaired = engine.repair(packet, repair_note="manual")
    assert repaired.output_packet is not None

    redact_source = VerifierPacket.minimal()
    redact_source.extension["origin"] = "hidden"
    redact_source.circulation_status = None
    redacted = engine.redact(redact_source, fields=("origin",))
    assert not redacted.boundary_safety.passed

    malformed = VerifierPacket(
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
    report = engine._finalize(
        PacketOperationName.REPAIR,
        (VerifierPacket.minimal(),),
        malformed,
        reason="malformed",
    )
    assert not report.residual_totality.passed
    assert not report.lineage_laundering.passed


def test_packet_operation_private_branches_preserve_or_report_losses() -> None:
    engine = PacketOperationEngine()
    parent = VerifierPacket.minimal()
    parent.scope = None
    specialized = engine.specialize(parent, scope="ignored")
    assert specialized.output_packet is not None

    left = VerifierPacket.minimal()
    left.origin = None
    left.boundary_refs = None
    duplicate = ResidualRecord(ResidualKind.UNRESOLVED, left.packet_id, ("dup",), "dup")
    left.residual_obligations.append(duplicate)
    right = VerifierPacket.minimal()
    right.residual_obligations.append(duplicate)
    composed = engine.compose(left, right)
    assert composed.output_packet is not None
    assert composed.output_packet.boundary_refs is not None

    contrast_left = VerifierPacket.minimal()
    contrast_right = VerifierPacket.minimal()
    contrast_left.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, "left", ("s",), "left")
    )
    contrast_right.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, "right", ("s",), "right")
    )
    contrasted = engine.contrast(contrast_left, contrast_right)
    assert contrasted.output_packet is not None
    assert len(contrasted.output_packet.residual_obligations) >= 2

    repair_source = VerifierPacket.minimal()
    repair_source.origin = None
    assert engine.repair(repair_source, repair_note="fix").output_packet is not None

    internalize_source = VerifierPacket.from_external_candidate()
    internalize_source.circulation_status = None
    assert engine.internalize(internalize_source, translated=False, boundary_checked=False)

    input_with_residual = VerifierPacket.minimal()
    input_with_residual.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, "input", ("s",), "preserve")
    )
    output_without_residual = VerifierPacket.minimal()
    assert not engine._check_core_monotonicity(
        (input_with_residual,), output_without_residual
    ).passed

    no_lineage = VerifierPacket.minimal()
    no_lineage.origin.lineage = []
    assert not engine._check_lineage_laundering(
        (VerifierPacket.minimal(), VerifierPacket.minimal()), no_lineage
    ).passed

    child = VerifierPacket.minimal()
    child.origin = None
    child.boundary_refs = None
    engine._preserve_parent_context(child, (VerifierPacket.minimal(),))
    assert child.origin is not None
    assert child.boundary_refs is not None


def test_ecological_invariant_check_covers_boundary_and_hook_losses() -> None:
    engine = PacketOperationEngine()
    parent = VerifierPacket.minimal()
    parent.boundary_refs = BoundaryRefs(destructive_boundary_ref="boundary")
    parent.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, parent.packet_id, ("scope",), "preserve")
    )
    child = VerifierPacket.minimal()
    child.origin = None
    child.boundary_refs = BoundaryRefs()
    child.residual_hooks = None
    child.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, child.packet_id, ("other",), "kept")
    )

    result = engine._check_ecological_invariants((parent,), child, boundary_checked=True)

    assert not result.passed

    parent.ecological_invariants.preserve_residuals = False
    parent.ecological_invariants.preserve_boundaries = False
    parent.ecological_invariants.preserve_counter_packet_route = False
    child.residual_hooks = None
    child.residual_obligations = []
    assert engine._check_ecological_invariants((parent,), child, boundary_checked=True)
