"""Reporter port."""

from __future__ import annotations

from typing import Protocol


class Reporter(Protocol):
    def emit(self, report: dict[str, object]) -> None: ...
