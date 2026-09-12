"""Opt-in integration through existing ecology storage, history and residual ports."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from verification_ecology_kit.capacity.checker import Snapshot, check_plan
from verification_ecology_kit.capacity.model import Contract, digest, require
from verification_ecology_kit.capacity.reducer import replay
from verification_ecology_kit.capacity.selector import plan
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.records import ConformanceProfile, ResidualKind
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.ports.storage import EcologyStore
from verification_ecology_kit.references import ObjectEnvelope, SchemaCatalogue
from verification_ecology_kit.runtime.loop import DefaultPacketGenerator


class CapacityRuntime:
    """One serialized writer only; JsonStore atomically replaces the whole ecology.

    Source residual digests are rechecked at every apply. Plan and inspect are read-only.
    No method dispatches tools, grants authority or discharges source residuals.
    """

    def __init__(self, store: EcologyStore, contract: Contract):
        self.store, self.contract = store, contract

    def _load(self) -> tuple[list[dict[str, Any]], Snapshot]:
        archive = self.store.load().archive.get("capacity_v1", {})
        require(
            not archive or archive["contract_digest"] == self.contract.contract_digest,
            "contract substitution; use a distinct ecology namespace",
        )
        events = archive.get("events", [])
        return events, replay(self.contract, events)

    def inspect(self) -> Snapshot:
        return self._load()[1]

    def plan(self) -> dict[str, Any]:
        self._check_sources()
        result = plan(self.contract, self.inspect())
        check_plan(self.contract, self.inspect(), result)
        return result

    def _check_sources(self) -> None:
        state = self.store.load()
        for work in self.contract.work:
            residual = state.residual_ledger.residuals.get(work.residual_id)
            require(
                residual is not None and residual.status.value == "active",
                "registered source residual is absent/inactive",
            )
            assert residual is not None
            require(digest(residual.to_dict()) == work.subject_digest, "source residual changed")
            require(self.contract.scope in residual.scope, "cross-scope work")

    def update(self, event: dict[str, Any]) -> Snapshot:
        event = deepcopy(event)
        events, before = self._load()
        if event["kind"] in {"apply", "dispatch", "result"}:
            self._check_sources()
        # Validate the entire proposed history before touching the store, including
        # conflicting retry detection. Deepcopy protects InMemoryStore on failure.
        after = replay(self.contract, [*events, event])
        if after.revision == before.revision:
            return after
        state = deepcopy(self.store.load())
        if event["kind"] == "result":
            envelope = ObjectEnvelope(
                event["payload"]["result_id"], "capacity-result", "1", event["payload"]
            )
            envelope.refresh_digest()
            bundle = VetBundle(
                "capacity-admission",
                "1",
                ConformanceProfile.CORE,
                SchemaCatalogue("capacity-catalogue", {"capacity-result": ("1",)}),
                objects=[envelope],
            )
            evidence = ConformanceEngine().run(bundle)
            require(evidence.decision.value == "accept", "existing evidence conformance failed")
            state.history.append("capacity_evidence_conformance", evidence.to_dict())
        for wid in after.repair - before.repair:
            work = next(w for w in self.contract.work if w.work_id == wid)
            repair = ResidualRecord(
                residual_id="capacity-repair-" + digest([self.contract.contract_digest, wid])[:24],
                kind=ResidualKind.UNEXCLUDED,
                origin=work.residual_id,
                scope=(self.contract.scope,),
                obligation=f"Repair/revalidate after negative check {wid}",
                exposure="blocks_authority",
                provenance=(event["event_id"],),
            )
            state.residual_ledger.add(repair, justification="capacity negative check repair")
        generated = state.archive.get("capacity_followups_v1", {})
        for wid in after.completed.keys() - before.completed.keys():
            work = next(w for w in self.contract.work if w.work_id == wid)
            key = digest(
                [
                    work.residual_id,
                    work.subject_digest,
                    work.input_digest,
                    work.rule_version,
                    work.check,
                ]
            )
            if key not in generated:
                residual = state.residual_ledger.residuals[work.residual_id]
                packets = DefaultPacketGenerator().from_residual(residual)
                for packet in packets:
                    packet.ensure_core_accountability()
                    packet.ensure_semantic_accountability()
                    state.add_packet(packet)
                generated[key] = [p.packet_id for p in packets]
        state.archive["capacity_followups_v1"] = generated
        state.archive["capacity_v1"] = {
            "contract_digest": self.contract.contract_digest,
            "events": [*events, event],
        }
        state.history.append(
            "capacity_event",
            {"event_digest": digest(event), "revision": after.revision, "authority_effect": "none"},
        )
        self.store.save(state)
        return after

    def event(self, kind: str, payload: dict[str, Any], event_id: str) -> Snapshot:
        return self.update(
            {
                "event_id": event_id,
                "revision": self.inspect().revision,
                "kind": kind,
                "payload": payload,
            }
        )
