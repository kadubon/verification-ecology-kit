"""Internalize packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def internalize(
    packet: VerifierPacket,
    *,
    translated: bool,
    boundary_checked: bool,
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).internalize(
        packet,
        translated=translated,
        boundary_checked=boundary_checked,
    )


__all__ = ["PacketOperationEngine", "internalize"]
