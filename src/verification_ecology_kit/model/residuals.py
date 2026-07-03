"""Residual records, routes, and liveness checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.records import (
    LedgerStatus,
    ResidualKind,
    ResidualMetabolismRoute,
    jsonable,
)
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result


@dataclass(frozen=True)
class ResidualRoute:
    owner: str
    deadline: str
    resource_quota: tuple[str, ...]
    recheck_trigger: str
    route_type: ResidualMetabolismRoute = ResidualMetabolismRoute.EXPLICIT_PRESERVED_UNKNOWN
    authority_effect: str = "informational"
    active_follow_through: bool = True
    preservation_reason: str = ""

    def is_live(self, *, now: datetime | None = None) -> bool:
        if not isinstance(self.route_type, ResidualMetabolismRoute):
            return False
        if not self.owner.strip():
            return False
        if not self.active_follow_through:
            return False
        if not self.resource_quota:
            return False
        if not self.recheck_trigger.strip():
            return False
        if not self.deadline:
            return False
        current = now or datetime.now(UTC)
        try:
            deadline = datetime.fromisoformat(self.deadline.replace("Z", "+00:00"))
        except ValueError:
            return False
        return deadline >= current


@dataclass
class ResidualRecord:
    kind: ResidualKind
    origin: str
    scope: tuple[str, ...]
    obligation: str
    payload: dict[str, Any] = field(default_factory=dict)
    exposure: str = "informational"
    status: LedgerStatus = LedgerStatus.ACTIVE
    route: ResidualRoute | None = None
    update_links: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    residual_id: str = field(default_factory=lambda: new_id("res"))

    def to_dict(self) -> dict[str, Any]:
        return jsonable(self)


@dataclass
class SoundGapResidual(ResidualRecord):
    certificate_ref: str = ""
    semantic_target: str = ""
    operational_claim: str = ""

    @classmethod
    def create(
        cls,
        *,
        certificate_ref: str,
        gap_kind: str,
        semantic_target: str,
        operational_claim: str,
        route: ResidualRoute,
        authority_effect: str = "blocks_authority",
    ) -> SoundGapResidual:
        return cls(
            kind=ResidualKind.SOUNDNESS_GAP,
            origin=certificate_ref,
            scope=(gap_kind,),
            obligation=f"Route and recheck soundness gap: {gap_kind}",
            route=route,
            exposure=authority_effect,
            certificate_ref=certificate_ref,
            semantic_target=semantic_target,
            operational_claim=operational_claim,
        )


def check_residual_liveness(
    residual: ResidualRecord,
    *,
    now: datetime | None = None,
) -> CheckResult:
    if residual.status in {LedgerStatus.RETIRED, LedgerStatus.REDACTED, LedgerStatus.MERGED}:
        return pass_result("LivenessOK")
    if residual.route is None or not residual.route.is_live(now=now):
        return residual_result(
            "LivenessOK",
            FailureCode.RESIDUAL_NOT_LIVE,
            residual_refs=(residual.residual_id,),
            suggested_repair_hooks=("assign_owner_deadline_quota_and_recheck_trigger",),
        )
    return pass_result("LivenessOK", evidence_refs=(residual.residual_id,))
