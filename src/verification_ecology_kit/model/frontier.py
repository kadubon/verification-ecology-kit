"""Verifiable frontier profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from verification_ecology_kit.model.records import jsonable


class FrontierComparison(StrEnum):
    EXPANDED = "expanded"
    REFINED = "refined"
    UNCHANGED = "unchanged"
    REGRESSED = "regressed"
    PACKET_SPAM = "packet_spam"


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

    def compare(
        self,
        other: VerifiableFrontierProfile,
        *,
        before_packet_count: int = 0,
        after_packet_count: int = 0,
    ) -> FrontierComparison:
        before_handles = {entry.unknown_handle for entry in self.entries}
        after_handles = {entry.unknown_handle for entry in other.entries}
        if after_handles == before_handles:
            if after_packet_count > before_packet_count:
                return FrontierComparison.PACKET_SPAM
            return FrontierComparison.UNCHANGED
        if before_handles.issubset(after_handles):
            return FrontierComparison.EXPANDED
        if after_handles and after_handles.intersection(before_handles):
            return FrontierComparison.REFINED
        return FrontierComparison.REGRESSED

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
