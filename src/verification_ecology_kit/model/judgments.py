"""Judgment records and use contexts."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.contracts import JudgmentContract
from verification_ecology_kit.model.records import LifecycleStatus, jsonable
from verification_ecology_kit.references import ObjectRef
from verification_ecology_kit.result import CheckResult, FailureCode, fail_result, pass_result


@dataclass(frozen=True)
class UseContext:
    subject_ref: ObjectRef
    subject_pointer: str
    resolved_input_ref: ObjectRef
    scope: tuple[str, ...]
    action: str
    ledger_ref: str
    policy_id: str
    schema_version: str
    digest_algorithm_id: str
    canonical_input_ref: ObjectRef
    input_digest: Digest
    freshness_horizon: str
    resource_bounds: tuple[str, ...]
    clock_context: str

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


@dataclass
class JudgmentRecord:
    judgment_id: str
    judgment_kind: str
    subject: ObjectRef
    checker_or_policy_ref: str
    contract_version: str
    schema_version: str
    object_id: str
    canonical_digest: Digest
    use_context_ref: str
    canonical_input_ref: ObjectRef
    input_pointer: str
    input_digest: Digest
    digest_algorithm_id: str
    result: str
    jvalid_result: str = "not_checked"
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    assumptions: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    residuals: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    timestamp_or_clock: str = ""

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


def jvalid(record: JudgmentRecord, context: UseContext, contract: JudgmentContract) -> CheckResult:
    if record.judgment_kind != contract.judgment_kind:
        return fail_result("JValid", FailureCode.JUDGMENT_INVALID)
    if record.contract_version != contract.version:
        return fail_result("JValid", FailureCode.JUDGMENT_INVALID)
    if record.subject.object_id != context.subject_ref.object_id:
        return fail_result("JValid", FailureCode.JUDGMENT_INVALID)
    if record.input_digest.value != context.input_digest.value:
        return fail_result("JValid", FailureCode.DIGEST_MISMATCH)
    if record.result not in contract.allowed_results:
        return fail_result("JValid", FailureCode.JUDGMENT_INVALID)
    if record.status not in {LifecycleStatus.ACTIVE, LifecycleStatus.MIGRATED}:
        return fail_result("JValid", FailureCode.STATUS_BLOCKS_SUPPORT)
    record.jvalid_result = "pass"
    return pass_result("JValid", evidence_refs=(record.judgment_id,))
