"""Fork packet operation."""

from __future__ import annotations

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.operations.base import OperationReport, PacketOperationEngine


def fork(
    packet: VerifierPacket,
    *,
    reason: str = "fork",
    engine: PacketOperationEngine | None = None,
) -> OperationReport:
    return (engine or PacketOperationEngine()).fork(packet, reason=reason)


__all__ = ["PacketOperationEngine", "fork"]
