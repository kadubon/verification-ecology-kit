"""Redact packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def redact(
    packet: VerifierPacket,
    *,
    fields: tuple[str, ...],
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).redact(packet, fields=fields)


__all__ = ["PacketOperationEngine", "redact"]
