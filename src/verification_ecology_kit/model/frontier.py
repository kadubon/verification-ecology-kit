"""Verifiable frontier profile."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.model.records import jsonable


@dataclass(frozen=True)
class FrontierEntry:
    unknown_handle: str
    transformation_class: str
    packet_support: tuple[str, ...]
    residual_witnesses: tuple[str, ...]
    resource_bounds: tuple[str, ...]


@dataclass
class VerifiableFrontierProfile:
    entries: list[FrontierEntry] = field(default_factory=list)

    def add(self, entry: FrontierEntry) -> None:
        self.entries.append(entry)

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
