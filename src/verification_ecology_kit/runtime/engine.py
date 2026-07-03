"""Extensible runtime engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.overclosure import SchemaOverclosureDetector
from verification_ecology_kit.model.packets import CounterPacket
from verification_ecology_kit.model.reachability import ReachabilityCertificate
from verification_ecology_kit.model.records import ResidualKind, Visibility
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.model.serde import reachability_certificate_from_json
from verification_ecology_kit.ports.generator import PacketGenerator
from verification_ecology_kit.ports.policy import RuntimePolicy
from verification_ecology_kit.ports.storage import EcologyStore
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result
from verification_ecology_kit.runtime.in_memory import InMemoryStore
from verification_ecology_kit.runtime.loop import (
    DefaultPacketGenerator,
    RuntimeReport,
    RuntimeStage,
    residual_from_history_event,
)
from verification_ecology_kit.runtime.policies import DefaultRuntimePolicy


@dataclass
class RuntimeEngine:
    store: EcologyStore = field(default_factory=InMemoryStore)
    generator: PacketGenerator = field(default_factory=DefaultPacketGenerator)
    policy: RuntimePolicy = field(default_factory=DefaultRuntimePolicy)

    def run_once(self) -> RuntimeReport:
        state = self.store.load()
        report = RuntimeReport()
        existing_history_residuals = {
            (residual.origin, residual.scope)
            for residual in state.residual_ledger.residuals.values()
        }
        for event in state.history.events:
            residual = residual_from_history_event(event.event_type, event.payload, event.event_id)
            if residual is None:
                continue
            history_key = (residual.origin, residual.scope)
            if history_key not in existing_history_residuals:
                state.residual_ledger.add(
                    residual,
                    justification="runtime history residualization",
                    provenance=(event.event_id,),
                )
                existing_history_residuals.add(history_key)
        active_residuals = [
            residual
            for residual in state.residual_ledger.residuals.values()
            if residual.status.value == "active"
        ]
        for residual in active_residuals:
            for packet in self.generator.from_residual(residual):
                report.generated_from_residuals.append(
                    f"{residual.residual_id}->{packet.packet_id}"
                )
                created_core = packet.ensure_core_accountability()
                created_semantic = packet.ensure_semantic_accountability()
                report.inherited_residual_refs.extend(
                    packet.origin.inherited_residuals if packet.origin else ()
                )
                report.inherited_boundary_refs.extend(
                    packet.boundary_refs.inherited_boundary_refs if packet.boundary_refs else ()
                )
                report.anti_overclosure_gaps.extend(
                    item.residual_id
                    for item in created_semantic
                    if "anti_overclosure" in item.scope
                )
                validation_results = packet.validate()
                for result in validation_results:
                    report.stages.append(RuntimeStage(result.check_name, packet.packet_id, result))
                counter_packet = cast(CounterPacket, CounterPacket.minimal())
                counter_findings = counter_packet.inspect_target(packet)
                report.counter_packet_obligations.extend(
                    item.residual_id
                    for item in packet.residual_obligations
                    if item.kind == ResidualKind.MISSING_COUNTER
                )
                counter_result = (
                    pass_result("RuntimeCounterPacketCheck")
                    if not counter_findings
                    else residual_result(
                        "RuntimeCounterPacketCheck",
                        FailureCode.MISSING_COUNTER_PACKET,
                        residual_refs=tuple(
                            finding.residual_kind.value for finding in counter_findings
                        ),
                    )
                )
                report.stages.append(
                    RuntimeStage("counter_packet_check", packet.packet_id, counter_result)
                )
                schema_result = self._schema_overclosure_result(
                    packet, created_core=created_core, state=state
                )
                report.schema_checks.append(schema_result.to_dict())
                report.stages.append(
                    RuntimeStage("schema_overclosure_check", packet.packet_id, schema_result)
                )
                lineage_result = (
                    pass_result("RuntimeLineageCheck")
                    if packet.origin and (packet.origin.traces or packet.origin.parent_packets)
                    else residual_result("RuntimeLineageCheck", FailureCode.MIGRATION_LOSS)
                )
                report.lineage_checks.append(lineage_result.to_dict())
                report.stages.append(
                    RuntimeStage("lineage_laundering_check", packet.packet_id, lineage_result)
                )
                reachability_result = self._reachability_result(packet, state)
                report.reachability_checks.append(reachability_result.to_dict())
                report.stages.append(
                    RuntimeStage("reachability_check", packet.packet_id, reachability_result)
                )
                repair_result = (
                    pass_result("RuntimeRepairRetireCheck")
                    if packet.update_profile and packet.update_profile.retirement_conditions
                    else residual_result(
                        "RuntimeRepairRetireCheck",
                        FailureCode.RESIDUAL_NOT_LIVE,
                    )
                )
                report.repair_or_retire_decisions.append(repair_result.to_dict())
                report.stages.append(
                    RuntimeStage(
                        "repair_or_retirement_decision",
                        packet.packet_id,
                        repair_result,
                    )
                )
                if self.policy.should_quarantine(packet):
                    if packet.circulation_status is not None:
                        packet.circulation_status.visibility = Visibility.QUARANTINED
                    report.quarantined_packets.append(packet.packet_id)
                    quarantine_result = residual_result(
                        "RuntimeQuarantineDecision",
                        FailureCode.BOUNDARY_UNCHECKED,
                    )
                    report.quarantine_decisions.append(quarantine_result.to_dict())
                    report.stages.append(
                        RuntimeStage(
                            "quarantine_decision",
                            packet.packet_id,
                            quarantine_result,
                        )
                    )
                    aperture_debt = ResidualRecord(
                        kind=ResidualKind.APERTURE_DEBT,
                        origin=packet.packet_id,
                        scope=("runtime",),
                        obligation="Runtime quarantine requires boundary or translation follow-up",
                        exposure="informational",
                    )
                    state.residual_ledger.add(aperture_debt, justification="runtime aperture debt")
                    report.aperture_debts.append(aperture_debt.residual_id)
                    aperture_result = residual_result(
                        "RuntimeApertureUpdate",
                        FailureCode.OVERCLOSURE_RISK,
                        residual_refs=(aperture_debt.residual_id,),
                    )
                    report.aperture_updates.append(aperture_result.to_dict())
                else:
                    quarantine_result = pass_result("RuntimeQuarantineDecision")
                    report.quarantine_decisions.append(quarantine_result.to_dict())
                    report.stages.append(
                        RuntimeStage(
                            "quarantine_decision",
                            packet.packet_id,
                            quarantine_result,
                        )
                    )
                    aperture_result = pass_result("RuntimeApertureUpdate")
                    report.aperture_updates.append(aperture_result.to_dict())
                report.stages.append(
                    RuntimeStage("aperture_update", packet.packet_id, aperture_result)
                )
                frontier_result = pass_result(
                    "RuntimeFrontierUpdate",
                    evidence_refs=(residual.residual_id,),
                )
                report.frontier_updates.append(frontier_result.to_dict())
                report.stages.append(
                    RuntimeStage("frontier_update", packet.packet_id, frontier_result)
                )
                state.add_packet(packet)
                report.generated_packets.append(packet.packet_id)
            report.residuals_routed.append(residual.residual_id)
        report.finalize()
        state.history.append("runtime_report", report.to_dict())
        self.store.save(state)
        return report

    def _schema_overclosure_result(
        self,
        packet: Any,
        *,
        created_core: list[ResidualRecord],
        state: VerifierEcologyState,
    ) -> CheckResult:
        if created_core:
            return residual_result(
                "RuntimeSchemaCheck",
                FailureCode.MISSING_REQUIRED_CORE,
                residual_refs=tuple(item.residual_id for item in created_core),
            )
        result, residuals = SchemaOverclosureDetector().detect(
            schema_rejected_unknown=not packet.anti_overclosure.unknowns_to_preserve,
            suppressed_residuals=tuple(packet.anti_overclosure.schema_overclosure_residuals),
            dashboard_hid_component_failure=not packet.anti_overclosure.lineage_laundering_checks,
        )
        for residual in residuals:
            packet.residual_obligations.append(residual)
            if packet.residual_hooks is not None:
                packet.residual_hooks.unresolved_residual_refs.append(residual.residual_id)
            state.residual_ledger.add(residual, justification="runtime schema overclosure check")
        return result

    def _reachability_result(self, packet: Any, state: VerifierEcologyState) -> CheckResult:
        refs = (
            tuple(packet.boundary_refs.reachability_certificate_refs)
            if packet.boundary_refs
            else ()
        )
        if not refs:
            return residual_result(
                "RuntimeReachabilityCheck",
                FailureCode.BOUNDARY_UNCHECKED,
                suggested_repair_hooks=("attach_reachability_certificate",),
            )
        missing: list[str] = []
        for ref in refs:
            certificate = self._reachability_certificate(state, ref)
            if certificate is None:
                missing.append(ref)
                continue
            result = certificate.admissible_exclusion()
            if not result.passed:
                return result
        if missing:
            return residual_result(
                "RuntimeReachabilityCheck",
                FailureCode.BOUNDARY_UNCHECKED,
                residual_refs=tuple(missing),
                suggested_repair_hooks=("provide_reachability_certificate_material",),
            )
        return pass_result("RuntimeReachabilityCheck", evidence_refs=refs)

    def _reachability_certificate(
        self,
        state: VerifierEcologyState,
        certificate_ref: str,
    ) -> ReachabilityCertificate | None:
        certificates = state.archive.get("reachability_certificates")
        if not isinstance(certificates, dict):
            return None
        value = certificates.get(certificate_ref)
        if isinstance(value, ReachabilityCertificate):
            return value
        if isinstance(value, dict):
            return reachability_certificate_from_json(value)
        return None
