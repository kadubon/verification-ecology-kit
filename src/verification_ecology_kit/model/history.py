"""Append-only observable process history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.records import jsonable


@dataclass(frozen=True)
class HistoryEvent:
    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: new_id("hist"))
    predecessor_event_id: str | None = None
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass
class ObservableProcessHistory:
    events: list[HistoryEvent] = field(default_factory=list)

    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        provenance: tuple[str, ...] = (),
    ) -> HistoryEvent:
        predecessor = self.events[-1].event_id if self.events else None
        event = HistoryEvent(
            event_type=event_type,
            payload=payload,
            predecessor_event_id=predecessor,
            provenance=provenance,
        )
        self.events.append(event)
        return event

    def is_prefix_of(self, other: ObservableProcessHistory) -> bool:
        if len(self.events) > len(other.events):
            return False
        return [event.to_dict() for event in self.events] == [
            event.to_dict() for event in other.events[: len(self.events)]
        ]

    def to_dict(self) -> dict[str, Any]:
        return {"events": [event.to_dict() for event in self.events]}
