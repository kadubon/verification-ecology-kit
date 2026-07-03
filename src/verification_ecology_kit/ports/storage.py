"""Storage port."""

from __future__ import annotations

from typing import Protocol

from verification_ecology_kit.model.ecology_state import VerifierEcologyState


class EcologyStore(Protocol):
    def load(self) -> VerifierEcologyState: ...

    def save(self, state: VerifierEcologyState) -> None: ...
