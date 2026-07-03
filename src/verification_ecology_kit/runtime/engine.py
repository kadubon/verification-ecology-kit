"""Extensible runtime engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.model.records import ResidualKind, Visibility
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.ports.generator import PacketGenerator
from verification_ecology_kit.ports.policy import RuntimePolicy
from verification_ecology_kit.ports.storage import EcologyStore
from verification_ecology_kit.runtime.in_memory import InMemoryStore
from verification_ecology_kit.runtime.loop import (
    DefaultPacketGenerator,
    RuntimeReport,
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
                packet.validate()
                report.counter_packet_obligations.extend(
                    item.residual_id
                    for item in packet.residual_obligations
                    if item.kind == ResidualKind.MISSING_COUNTER
                )
                report.schema_checks.append(
                    "pass" if not created_core else f"residualized:{packet.packet_id}"
                )
                report.lineage_checks.append(
                    "pass"
                    if packet.origin and (packet.origin.traces or packet.origin.parent_packets)
                    else f"residualized:{packet.packet_id}"
                )
                report.reachability_checks.append(
                    "pass"
                    if packet.boundary_refs and packet.boundary_refs.reachability_certificate_refs
                    else f"residualized:{packet.packet_id}"
                )
                report.repair_or_retire_decisions.append(
                    "pass"
                    if packet.update_profile and packet.update_profile.retirement_conditions
                    else f"residualized:{packet.packet_id}"
                )
                if self.policy.should_quarantine(packet):
                    if packet.circulation_status is not None:
                        packet.circulation_status.visibility = Visibility.QUARANTINED
                    report.quarantined_packets.append(packet.packet_id)
                    report.quarantine_decisions.append(f"quarantine:{packet.packet_id}")
                    aperture_debt = ResidualRecord(
                        kind=ResidualKind.APERTURE_DEBT,
                        origin=packet.packet_id,
                        scope=("runtime",),
                        obligation="Runtime quarantine requires boundary or translation follow-up",
                        exposure="informational",
                    )
                    state.residual_ledger.add(aperture_debt, justification="runtime aperture debt")
                    report.aperture_debts.append(aperture_debt.residual_id)
                    report.aperture_updates.append(aperture_debt.residual_id)
                else:
                    report.quarantine_decisions.append(f"allow:{packet.packet_id}")
                    report.aperture_updates.append(f"unchanged:{packet.packet_id}")
                report.frontier_updates.append(f"routed:{residual.residual_id}")
                state.add_packet(packet)
                report.generated_packets.append(packet.packet_id)
            report.residuals_routed.append(residual.residual_id)
        report.finalize()
        state.history.append("runtime_report", report.to_dict())
        self.store.save(state)
        return report
