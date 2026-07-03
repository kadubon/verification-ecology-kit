"""JSON-file persistence for runtime state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.serde import ecology_state_from_json


class JsonStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> VerifierEcologyState:
        if not self.path.exists():
            return VerifierEcologyState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ecology_state_from_json(data)

    def save(self, state: VerifierEcologyState) -> None:
        _reject_symlink_target(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state.to_dict(), indent=2, sort_keys=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.path.parent,
            prefix=f".{self.path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(payload)
            handle.write("\n")
        try:
            _reject_symlink_target(self.path)
            os.replace(temp_path, self.path)
        finally:
            if temp_path.exists():
                temp_path.unlink()


def _reject_symlink_target(path: Path) -> None:
    parent = path.parent
    if parent.exists() and parent.is_symlink():
        raise ValueError(f"Refusing to write through symlinked directory: {parent}")
    if path.exists() and path.is_symlink():
        raise ValueError(f"Refusing to overwrite symlinked store path: {path}")
