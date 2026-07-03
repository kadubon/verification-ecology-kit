"""Policy port."""

from __future__ import annotations

from typing import Protocol

from verification_ecology_kit.model.packets import VerifierPacket


class RuntimePolicy(Protocol):
    def should_quarantine(self, packet: VerifierPacket) -> bool: ...
