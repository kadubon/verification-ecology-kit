"""Quarantine packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def quarantine(
    packet: VerifierPacket,
    *,
    reason: str,
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).quarantine(packet, reason=reason)


__all__ = ["PacketOperationEngine", "quarantine"]
