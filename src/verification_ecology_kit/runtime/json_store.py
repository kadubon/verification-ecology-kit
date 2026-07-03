"""JSON-file persistence for runtime state."""

from __future__ import annotations

import json
from pathlib import Path

from verification_ecology_kit.model.ecology_state import VerifierEcologyState


class JsonStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> VerifierEcologyState:
        if not self.path.exists():
            return VerifierEcologyState()
        # The current persistence format is intentionally conservative: it keeps raw JSON
        # in archive and lets explicit import adapters rebuild rich packet objects.
        data = json.loads(self.path.read_text(encoding="utf-8"))
        state = VerifierEcologyState()
        state.archive["json_store_snapshot"] = data
        return state

    def save(self, state: VerifierEcologyState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(state.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
        )
