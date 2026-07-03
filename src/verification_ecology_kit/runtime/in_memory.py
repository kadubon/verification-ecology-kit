"""In-memory runtime storage."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.model.ecology_state import VerifierEcologyState


@dataclass
class InMemoryStore:
    state: VerifierEcologyState = field(default_factory=VerifierEcologyState)

    def load(self) -> VerifierEcologyState:
        return self.state

    def save(self, state: VerifierEcologyState) -> None:
        self.state = state
