"""Packet generator port."""

from __future__ import annotations

from typing import Protocol

from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.residuals import ResidualRecord


class PacketGenerator(Protocol):
    def from_residual(self, residual: ResidualRecord) -> list[VerifierPacket]: ...
