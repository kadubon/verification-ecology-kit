"""Repair packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def repair(
    packet: VerifierPacket,
    *,
    repair_note: str,
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).repair(packet, repair_note=repair_note)


__all__ = ["PacketOperationEngine", "repair"]
