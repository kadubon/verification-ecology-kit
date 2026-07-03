"""Compose packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def compose(
    left: VerifierPacket,
    right: VerifierPacket,
    *,
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).compose(left, right)


__all__ = ["PacketOperationEngine", "compose"]
