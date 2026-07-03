"""Verifier ecology state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.model.history import ObservableProcessHistory
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import jsonable


@dataclass
class VerifierEcologyState:
    history: ObservableProcessHistory = field(default_factory=ObservableProcessHistory)
    packet_population: dict[str, VerifierPacket] = field(default_factory=dict)
    residual_ledger: ResidualLedger = field(default_factory=ResidualLedger)
    archive: dict[str, Any] = field(default_factory=dict)
    reusable_intelligence_capital: dict[str, Any] = field(default_factory=dict)

    def add_packet(self, packet: VerifierPacket) -> None:
        self.packet_population[packet.packet_id] = packet
        self.history.append("packet_added", {"packet_id": packet.packet_id})

    def to_dict(self) -> dict[str, object]:
        return jsonable(
            {
                "history": self.history.to_dict(),
                "packet_population": {
                    packet_id: packet.to_dict()
                    for packet_id, packet in sorted(self.packet_population.items())
                },
                "residual_ledger": self.residual_ledger.to_dict(),
                "archive": self.archive,
                "reusable_intelligence_capital": self.reusable_intelligence_capital,
            }
        )
