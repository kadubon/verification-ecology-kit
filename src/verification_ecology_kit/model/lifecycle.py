"""Lifecycle status events and deterministic status folding."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.records import LifecycleStatus, ResidualKind, jsonable
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result

STATUS_PRECEDENCE: dict[LifecycleStatus, int] = {
    LifecycleStatus.REVOKED: 4,
    LifecycleStatus.STALE: 3,
    LifecycleStatus.UNKNOWN: 3,
    LifecycleStatus.MIGRATED: 2,
    LifecycleStatus.ACTIVE: 1,
}


@dataclass(frozen=True)
class StatusEvent:
    object_id: str
    pre_status: LifecycleStatus
    post_status: LifecycleStatus
    cause: str
    actor_authority_ref: str
    ledger_event_ref: str
    invalidation_trigger: str = ""
    migration_target: str = ""
    residual_disposition: tuple[str, ...] = ()
    predecessor_event_ref: str | None = None
    provenance: tuple[str, ...] = ()
    status_event_id: str = field(default_factory=lambda: new_id("st"))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass(frozen=True)
class StatusView:
    object_id: str
    status: LifecycleStatus
    residuals: tuple[ResidualRecord, ...] = ()
    status_event_refs: tuple[str, ...] = ()


class StatusFold:
    def fold(self, object_id: str, events: list[StatusEvent]) -> tuple[StatusView, CheckResult]:
        relevant = [event for event in events if event.object_id == object_id]
        if not relevant:
            residual = self._status_residual(object_id, "missing status event")
            return (
                StatusView(object_id, LifecycleStatus.UNKNOWN, (residual,), ()),
                residual_result(
                    "StatusOK",
                    FailureCode.STATUS_BLOCKS_SUPPORT,
                    residual_refs=(residual.residual_id,),
                ),
            )
        seen: set[str] = set()
        residuals: list[ResidualRecord] = []
        current: LifecycleStatus | None = None
        for event in relevant:
            if event.predecessor_event_ref and event.predecessor_event_ref not in seen:
                residuals.append(
                    self._status_residual(object_id, "missing predecessor status event")
                )
                current = LifecycleStatus.UNKNOWN
            if event.post_status == LifecycleStatus.MIGRATED and not event.migration_target:
                residuals.append(self._status_residual(object_id, "missing migration target"))
                current = LifecycleStatus.UNKNOWN
            elif (
                current is None
                or STATUS_PRECEDENCE[event.post_status] >= STATUS_PRECEDENCE[current]
            ):
                current = event.post_status
            seen.add(event.status_event_id)
        refs = tuple(event.status_event_id for event in relevant)
        if residuals:
            return (
                StatusView(object_id, LifecycleStatus.UNKNOWN, tuple(residuals), refs),
                residual_result(
                    "StatusOK",
                    FailureCode.STATUS_BLOCKS_SUPPORT,
                    residual_refs=tuple(residual.residual_id for residual in residuals),
                ),
            )
        return StatusView(object_id, current or LifecycleStatus.UNKNOWN, (), refs), pass_result(
            "StatusOK", evidence_refs=refs
        )

    def _status_residual(self, object_id: str, reason: str) -> ResidualRecord:
        return ResidualRecord(
            kind=ResidualKind.UNRESOLVED,
            origin=object_id,
            scope=("lifecycle_status",),
            obligation=reason,
            exposure="blocks_support",
        )
