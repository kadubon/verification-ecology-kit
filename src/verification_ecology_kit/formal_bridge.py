"""Bridge Python VET operations to the formal VET-Core trace contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.digest import DigestPolicy
from verification_ecology_kit.model.records import ResidualKind, jsonable
from verification_ecology_kit.operations.base import OperationReport, PacketOperationName
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result
from verification_ecology_kit.runtime.loop import RuntimeStage

FORMAL_OPERATION_NAMES: frozenset[str] = frozenset(
    {
        "fork",
        "specialize",
        "generalize",
        "compose",
        "contrast",
        "repair",
        "retire",
        "quarantine",
        "internalize",
        "redact",
    }
)

FORMAL_RUNTIME_STAGES: frozenset[str] = frozenset(
    {
        "candidate_generation",
        "core_accountability",
        "semantic_accountability",
        "residual_metabolism",
        "packet_generation",
        "counter_packet_check",
        "boundary_check",
        "reachability_check",
        "schema_overclosure_check",
        "lineage_check",
        "authority_check",
        "quarantine_decision",
        "internalization_decision",
        "repair_decision",
        "retirement_decision",
        "aperture_update",
        "frontier_update",
        "lineage_laundering_check",
        "repair_or_retirement_decision",
    }
)


@dataclass(frozen=True)
class FormalStageTrace:
    stage: str
    subject_ref: str
    decision: str
    evidence_refs: tuple[str, ...] = ()
    residual_refs: tuple[str, ...] = ()
    authority_effect: str = ""

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class FormalTrace:
    trace_id: str
    formal_semantics_version: str
    before_state: dict[str, Any]
    operation: str
    after_state: dict[str, Any]
    residual_deltas: tuple[dict[str, Any], ...] = ()
    boundary_deltas: tuple[dict[str, Any], ...] = ()
    authority_deltas: tuple[dict[str, Any], ...] = ()
    aperture_deltas: tuple[dict[str, Any], ...] = ()
    frontier_deltas: tuple[dict[str, Any], ...] = ()
    stages: tuple[FormalStageTrace, ...] = ()
    invariant_checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)

    def digest(self) -> str:
        return DigestPolicy().digest_json(self.to_dict()).value


@dataclass(frozen=True)
class FormalSemanticsReport:
    trace_id: str
    formal_operation_exists: bool
    preconditions_match: bool
    expected_residuals_present: bool
    expected_boundaries_present: bool
    expected_authority_blockers_present: bool
    invariant_checks_pass: bool
    report_digest: str
    findings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.formal_operation_exists
            and self.preconditions_match
            and self.expected_residuals_present
            and self.expected_boundaries_present
            and self.expected_authority_blockers_present
            and self.invariant_checks_pass
        )

    def to_check_result(self) -> CheckResult:
        if self.passed:
            return pass_result("FormalTraceConformance", evidence_refs=(self.report_digest,))
        return residual_result(
            "FormalTraceConformance",
            FailureCode.MIGRATION_LOSS,
            suggested_repair_hooks=("align_python_trace_with_formal_vet_core_semantics",),
        )

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


def export_operation_trace(
    *,
    before_state: dict[str, Any],
    report: OperationReport,
    after_state: dict[str, Any] | None = None,
) -> FormalTrace:
    """Export a deterministic formal trace for a packet operation report."""

    output = report.output_packet.to_dict() if report.output_packet is not None else {}
    after = after_state or {"output_packet": output}
    residual_deltas = tuple(
        _residual_delta(item) for item in output.get("residual_obligations", ())
    )
    boundary_deltas = _boundary_deltas(output)
    invariant_checks = (
        jsonable(report.ecological_invariant_check)
        if report.ecological_invariant_check is not None
        else {}
    )
    trace = FormalTrace(
        trace_id=_trace_id(report.operation.value, before_state, after),
        formal_semantics_version="vet-core-1.2.0",
        before_state=before_state,
        operation=report.operation.value,
        after_state=after,
        residual_deltas=residual_deltas,
        boundary_deltas=boundary_deltas,
        authority_deltas=_authority_deltas(report),
        aperture_deltas=_aperture_deltas(report),
        frontier_deltas=_frontier_deltas(report),
        invariant_checks={
            key: value for key, value in invariant_checks.items() if isinstance(value, bool)
        },
    )
    return trace


def export_runtime_stage_trace(stage: RuntimeStage) -> FormalStageTrace:
    return FormalStageTrace(
        stage=stage.stage_name,
        subject_ref=stage.packet_id,
        decision=stage.decision or stage.check_result.result.value,
        evidence_refs=tuple(stage.evidence_refs or list(stage.check_result.evidence_refs)),
        residual_refs=tuple(stage.residual_refs or list(stage.check_result.residual_refs)),
        authority_effect=stage.authority_effect,
    )


def check_formal_trace(trace: FormalTrace) -> FormalSemanticsReport:
    findings: list[str] = []
    operation_exists = trace.operation in FORMAL_OPERATION_NAMES
    if not operation_exists:
        findings.append(f"unknown operation: {trace.operation}")
    expected_residuals = _expected_residuals_present(trace)
    if not expected_residuals:
        findings.append("required residual obligation is missing")
    expected_boundaries = _expected_boundaries_present(trace)
    if not expected_boundaries:
        findings.append("boundary consequence is missing")
    authority_blockers = _expected_authority_blockers_present(trace)
    if not authority_blockers:
        findings.append("authority blocker is missing")
    invariants_pass = (
        all(trace.invariant_checks.values()) if trace.invariant_checks else True
    ) or bool(trace.residual_deltas)
    report_payload = {
        "trace_id": trace.trace_id,
        "operation": trace.operation,
        "findings": findings,
    }
    return FormalSemanticsReport(
        trace_id=trace.trace_id,
        formal_operation_exists=operation_exists,
        preconditions_match=bool(trace.before_state) and bool(trace.after_state),
        expected_residuals_present=expected_residuals,
        expected_boundaries_present=expected_boundaries,
        expected_authority_blockers_present=authority_blockers,
        invariant_checks_pass=invariants_pass,
        report_digest=DigestPolicy().digest_json(report_payload).value,
        findings=tuple(findings),
    )


def check_runtime_stage_trace(stage: FormalStageTrace) -> FormalSemanticsReport:
    operation_exists = stage.stage in FORMAL_RUNTIME_STAGES
    findings = [] if operation_exists else [f"unknown runtime stage: {stage.stage}"]
    report_payload = {"stage": stage.to_dict(), "findings": findings}
    return FormalSemanticsReport(
        trace_id=f"stage:{stage.stage}:{stage.subject_ref}",
        formal_operation_exists=operation_exists,
        preconditions_match=bool(stage.subject_ref),
        expected_residuals_present=True,
        expected_boundaries_present=True,
        expected_authority_blockers_present=True,
        invariant_checks_pass=True,
        report_digest=DigestPolicy().digest_json(report_payload).value,
        findings=tuple(findings),
    )


def _trace_id(operation: str, before_state: dict[str, Any], after_state: dict[str, Any]) -> str:
    digest = DigestPolicy().digest_json(
        {"operation": operation, "before_state": before_state, "after_state": after_state}
    )
    return f"formal-trace-{digest.value[:16]}"


def _residual_delta(raw: Any) -> dict[str, Any]:
    item = raw if isinstance(raw, dict) else {}
    return {
        "residual_id": str(item.get("residual_id", "")),
        "kind": str(item.get("kind", "")),
        "origin": str(item.get("origin", "")),
        "scope": item.get("scope", []),
        "exposure": str(item.get("exposure", "")),
        "route": item.get("route"),
    }


def _boundary_deltas(output_packet: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    boundary = output_packet.get("boundary_refs")
    if not isinstance(boundary, dict):
        return ()
    refs = {
        "destructive_boundary_ref": boundary.get("destructive_boundary_ref", ""),
        "narrowing_boundary_ref": boundary.get("narrowing_boundary_ref", ""),
        "reachability_certificate_refs": boundary.get("reachability_certificate_refs", []),
        "inherited_boundary_refs": boundary.get("inherited_boundary_refs", []),
    }
    if any(bool(value) for value in refs.values()):
        return (refs,)
    return ()


def _authority_deltas(report: OperationReport) -> tuple[dict[str, Any], ...]:
    blockers = [
        residual_id
        for residual_id in report.residual_refs
        if report.boundary_safety.result.value != "pass"
        or report.ecological_invariants.result.value != "pass"
    ]
    if not blockers:
        return ()
    return ({"authority_effect": "blocks_or_residualizes_authority", "residual_refs": blockers},)


def _aperture_deltas(report: OperationReport) -> tuple[dict[str, Any], ...]:
    if report.operation is PacketOperationName.GENERALIZE:
        return ({"comparison": "aperture_debt_required_for_generalization"},)
    return ()


def _frontier_deltas(report: OperationReport) -> tuple[dict[str, Any], ...]:
    if report.operation is PacketOperationName.COMPOSE:
        return ({"comparison": "composition_not_frontier_acceleration_by_count"},)
    return ()


def _expected_residuals_present(trace: FormalTrace) -> bool:
    kinds = {item.get("kind") for item in trace.residual_deltas}
    if trace.operation == "compose":
        return {ResidualKind.UNEXCLUDED.value, ResidualKind.MISSING_COUNTER.value}.issubset(kinds)
    if trace.operation == "generalize":
        return ResidualKind.UNEXCLUDED.value in kinds or ResidualKind.APERTURE_DEBT.value in kinds
    if trace.operation == "redact":
        return ResidualKind.REDACTION_RESIDUAL.value in kinds
    return True


def _expected_boundaries_present(trace: FormalTrace) -> bool:
    if trace.operation in {"compose", "generalize"}:
        kinds = {item.get("kind") for item in trace.residual_deltas}
        return bool(trace.boundary_deltas) or ResidualKind.UNEXCLUDED.value in kinds
    return True


def _expected_authority_blockers_present(trace: FormalTrace) -> bool:
    if trace.operation in {"compose", "generalize", "redact"}:
        return bool(trace.authority_deltas or trace.residual_deltas)
    return True
