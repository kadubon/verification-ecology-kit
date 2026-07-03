"""Generalize packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def generalize(
    packet: VerifierPacket,
    *,
    residualize_scope_loss: bool = True,
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).generalize(
        packet,
        residualize_scope_loss=residualize_scope_loss,
    )


__all__ = ["PacketOperationEngine", "generalize"]
