from __future__ import annotations

from jsonschema import Draft202012Validator

from verification_ecology_kit.formal_bridge import (
    check_formal_trace,
    check_runtime_stage_trace,
    export_operation_trace,
    export_runtime_stage_trace,
)
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.result import pass_result
from verification_ecology_kit.runtime.loop import RuntimeStage


def test_operation_trace_export_is_deterministic() -> None:
    engine = PacketOperationEngine()
    left = VerifierPacket.minimal()
    right = VerifierPacket.minimal()
    report = engine.compose(left, right)
    before = {"packets": [left.to_dict(), right.to_dict()]}

    trace = export_operation_trace(before_state=before, report=report)
    again = export_operation_trace(before_state=before, report=report)

    assert trace.to_dict() == again.to_dict()
    assert trace.digest() == again.digest()
    conformance = check_formal_trace(trace)
    assert conformance.passed, conformance.findings


def test_formal_stage_trace_export() -> None:
    stage = RuntimeStage("reachability_check", "pkt-1", pass_result("RuntimeReachabilityCheck"))
    trace = export_runtime_stage_trace(stage)
    report = check_runtime_stage_trace(trace)
    assert report.passed, report.findings
    assert trace.stage == "reachability_check"
    assert trace.subject_ref == "pkt-1"


def test_formal_trace_schema_shape() -> None:
    engine = PacketOperationEngine()
    packet = VerifierPacket.minimal()
    report = engine.generalize(packet)
    trace = export_operation_trace(before_state={"packets": [packet.to_dict()]}, report=report)
    schema = {
        "type": "object",
        "required": ["trace_id", "formal_semantics_version", "operation", "residual_deltas"],
        "properties": {
            "trace_id": {"type": "string"},
            "formal_semantics_version": {"type": "string"},
            "operation": {"type": "string"},
            "residual_deltas": {"type": "array"},
        },
    }
    Draft202012Validator(schema).validate(trace.to_dict())
