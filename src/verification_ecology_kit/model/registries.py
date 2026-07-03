"""Carrier, checker, and contract registries."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.model.contracts import CarrierContract, CheckerContract
from verification_ecology_kit.model.records import LifecycleStatus, jsonable
from verification_ecology_kit.result import (
    CheckResult,
    FailureCode,
    fail_result,
    pass_result,
    residual_result,
)


@dataclass
class CarrierRegistryEntry:
    carrier_id: str
    kind: str
    domain: str
    codomain: str
    checker_id: str
    version: str
    trust_basis: tuple[str, ...] = ()
    invalidation_conditions: tuple[str, ...] = ()
    contract: CarrierContract | None = None
    migration_witness_ref: str = ""
    compatibility_relation: str = ""
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    acceptance_judgment_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


@dataclass
class CheckerRegistryEntry:
    checker_id: str
    checker_type: str
    checker_version: str
    contract: CheckerContract | None = None
    trust_basis: tuple[str, ...] = ()
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    sandbox_status: str = "not_required"
    delegation_basis: tuple[str, ...] = ()
    human_assessment_role: str = ""
    tool_assessment_role: str = ""
    invalidation_conditions: tuple[str, ...] = ()
    recheck_trigger: str = ""
    acceptance_judgment_ref: str = ""

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


@dataclass
class CarrierRegistry:
    entries: dict[str, CarrierRegistryEntry] = field(default_factory=dict)

    def accept(self, carrier_id: str) -> CheckResult:
        entry = self.entries.get(carrier_id)
        if entry is None:
            return fail_result("AcceptCarrier", FailureCode.UNRESOLVED_REFERENCE)
        if entry.status == LifecycleStatus.ACTIVE:
            return pass_result("AcceptCarrier", evidence_refs=(carrier_id,))
        if entry.status == LifecycleStatus.MIGRATED and entry.migration_witness_ref:
            return pass_result("AcceptCarrier", evidence_refs=(entry.migration_witness_ref,))
        return residual_result(
            "AcceptCarrier",
            FailureCode.STATUS_BLOCKS_SUPPORT,
            residual_refs=(carrier_id,),
        )


@dataclass
class CheckerRegistry:
    entries: dict[str, CheckerRegistryEntry] = field(default_factory=dict)

    def accept(self, checker_id: str) -> CheckResult:
        entry = self.entries.get(checker_id)
        if entry is None:
            return fail_result("AcceptChecker", FailureCode.UNRESOLVED_REFERENCE)
        if entry.status == LifecycleStatus.ACTIVE:
            return pass_result("AcceptChecker", evidence_refs=(checker_id,))
        if entry.status == LifecycleStatus.MIGRATED and entry.acceptance_judgment_ref:
            return pass_result("AcceptChecker", evidence_refs=(entry.acceptance_judgment_ref,))
        return residual_result(
            "AcceptChecker",
            FailureCode.STATUS_BLOCKS_SUPPORT,
            residual_refs=(checker_id,),
        )
