from __future__ import annotations

from collections.abc import Callable

import pytest

from verification_ecology_kit.formal_bridge import check_formal_trace, export_operation_trace
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def _packet() -> VerifierPacket:
    packet = VerifierPacket.minimal()
    packet.counter_packet_refs.append("counter-local")
    if packet.update_profile is not None:
        packet.update_profile.retirement_conditions.append("manual_reinspection")
    packet.anti_overclosure.unknowns_to_preserve.append("future_candidate")
    packet.anti_overclosure.lineage_laundering_checks.append("visible_parent_trace")
    packet.residual_liveness.owner = "owner"
    packet.residual_liveness.recheck_trigger = "manual_recheck"
    return packet


def _operation_cases() -> list[tuple[str, Callable[[PacketOperationEngine], OperationReport]]]:
    return [
        ("fork", lambda engine: engine.fork(_packet())),
        ("specialize", lambda engine: engine.specialize(_packet(), scope="narrow")),
        ("generalize", lambda engine: engine.generalize(_packet())),
        ("compose", lambda engine: engine.compose(_packet(), _packet())),
        ("contrast", lambda engine: engine.contrast(_packet(), _packet())),
        ("repair", lambda engine: engine.repair(_packet(), repair_note="repair residual")),
        ("retire", lambda engine: engine.retire(_packet(), reason="superseded")),
        ("quarantine", lambda engine: engine.quarantine(_packet(), reason="low trust")),
        (
            "internalize",
            lambda engine: engine.internalize(
                VerifierPacket.from_external_candidate(),
                translated=False,
                boundary_checked=False,
            ),
        ),
        ("redact", lambda engine: engine.redact(_packet(), fields=("origin",))),
    ]


@pytest.mark.parametrize(("operation_name", "factory"), _operation_cases())
def test_packet_operations_export_formal_conformance_traces(
    operation_name: str,
    factory: Callable[[PacketOperationEngine], OperationReport],
) -> None:
    engine = PacketOperationEngine()
    report = factory(engine)
    trace = export_operation_trace(
        before_state={"operation": operation_name, "inputs": list(report.input_packet_ids)},
        report=report,
    )
    conformance = check_formal_trace(trace)
    assert trace.operation == operation_name
    assert conformance.passed, conformance.findings


def test_compose_trace_contains_boundary_and_counter_obligations() -> None:
    engine = PacketOperationEngine()
    report = engine.compose(_packet(), _packet())
    trace = export_operation_trace(
        before_state={"operation": "compose", "inputs": list(report.input_packet_ids)},
        report=report,
    )
    kinds = {item["kind"] for item in trace.residual_deltas}
    assert {"unexcluded", "missing_counter"}.issubset(kinds)
    assert check_formal_trace(trace).passed
