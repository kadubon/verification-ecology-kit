"""JSON-file persistence for runtime state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.history import HistoryEvent, ObservableProcessHistory


class JsonStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> VerifierEcologyState:
        if not self.path.exists():
            return VerifierEcologyState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return _state_from_json(data)

    def save(self, state: VerifierEcologyState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
        )


def _state_from_json(data: Any) -> VerifierEcologyState:
    if not isinstance(data, dict):
        state = VerifierEcologyState()
        state.archive["json_store_snapshot"] = data
        return state

    state = VerifierEcologyState()
    state.history = _history_from_json(data.get("history", {}))

    from verification_ecology_kit.cli import _ledger_from_json, _packet_from_json

    population = data.get("packet_population", {})
    if isinstance(population, dict):
        for packet_data in population.values():
            packet = _packet_from_json(packet_data)
            state.packet_population[packet.packet_id] = packet

    ledger_data = data.get("residual_ledger")
    if isinstance(ledger_data, dict):
        state.residual_ledger = _ledger_from_json(ledger_data)

    archive = data.get("archive")
    if isinstance(archive, dict):
        state.archive = archive
    capital = data.get("reusable_intelligence_capital")
    if isinstance(capital, dict):
        state.reusable_intelligence_capital = capital
    return state


def _history_from_json(data: Any) -> ObservableProcessHistory:
    if not isinstance(data, dict):
        return ObservableProcessHistory()
    events = data.get("events", [])
    if not isinstance(events, list):
        return ObservableProcessHistory()
    history = ObservableProcessHistory()
    for item in events:
        if not isinstance(item, dict):
            continue
        predecessor = item.get("predecessor_event_id")
        payload = item.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        history.events.append(
            HistoryEvent(
                event_type=str(item.get("event_type", "unknown")),
                payload=payload,
                event_id=str(item.get("event_id", "")),
                predecessor_event_id=str(predecessor) if predecessor is not None else None,
                provenance=tuple(str(value) for value in item.get("provenance", ())),
            )
        )
    return history
