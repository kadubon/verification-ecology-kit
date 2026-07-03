"""Carrier, checker, and judgment contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.model.records import LifecycleStatus
from verification_ecology_kit.result import CheckOutcome


@dataclass(frozen=True)
class CarrierContract:
    contract_id: str
    kind: str
    domain: str
    codomain: str
    accepted_versions: tuple[str, ...]
    invalidation_conditions: tuple[str, ...] = ()
    migration_witness_required: bool = True


@dataclass(frozen=True)
class CheckerContract:
    contract_id: str
    checker_type: str
    accepted_versions: tuple[str, ...]
    accepted_statuses: tuple[LifecycleStatus, ...] = (LifecycleStatus.ACTIVE,)
    sandbox_required: bool = False
    invalidation_conditions: tuple[str, ...] = ()
    recheck_trigger: str = ""


@dataclass(frozen=True)
class JudgmentContract:
    judgment_kind: str
    subject_type: str
    input_digest_type: str
    checker_or_policy_type: str
    result_type: str
    allowed_results: tuple[str, ...] = (
        CheckOutcome.PASS.value,
        CheckOutcome.FAIL.value,
        CheckOutcome.RESIDUALIZE.value,
    )
    freshness_interval: str = ""
    invalidation_triggers: tuple[str, ...] = ()
    recheck_trigger: str = ""
    residual_schema_ref: str = ""
    version: str = "1"


@dataclass
class ContractRegistry:
    carrier_contracts: dict[str, CarrierContract] = field(default_factory=dict)
    checker_contracts: dict[str, CheckerContract] = field(default_factory=dict)
    judgment_contracts: dict[str, JudgmentContract] = field(default_factory=dict)

    def add_judgment_contract(self, contract: JudgmentContract) -> None:
        self.judgment_contracts[contract.judgment_kind] = contract
