"""Specialize packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def specialize(
    packet: VerifierPacket,
    *,
    scope: str,
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).specialize(packet, scope=scope)


__all__ = ["PacketOperationEngine", "specialize"]
