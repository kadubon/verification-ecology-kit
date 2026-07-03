from __future__ import annotations

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.contracts import JudgmentContract
from verification_ecology_kit.model.judgments import JudgmentRecord, UseContext, jvalid
from verification_ecology_kit.model.lifecycle import StatusEvent, StatusFold
from verification_ecology_kit.model.records import (
    LifecycleStatus,
    TypedPartialRecord,
    TypeEnvironment,
)
from verification_ecology_kit.references import ObjectRef


def _ref(object_id: str) -> ObjectRef:
    return ObjectRef("bundle", object_id, "schema", digest=Digest("sha256", "abc"))


def test_type_environment_and_partial_record() -> None:
    env = TypeEnvironment("env", {"field": "string"}, {}, {})
    record = TypedPartialRecord(env.environment_id, {"field": "value"})
    assert record.has_field("field")


def test_status_fold_precedence_revoked_wins() -> None:
    events = [
        StatusEvent(
            "obj", LifecycleStatus.UNKNOWN, LifecycleStatus.ACTIVE, "create", "actor", "ledger"
        ),
        StatusEvent(
            "obj", LifecycleStatus.ACTIVE, LifecycleStatus.REVOKED, "bad", "actor", "ledger"
        ),
    ]
    view, result = StatusFold().fold("obj", events)
    assert result.passed
    assert view.status == LifecycleStatus.REVOKED


def test_status_fold_missing_predecessor_unknowns() -> None:
    events = [
        StatusEvent(
            "obj",
            LifecycleStatus.ACTIVE,
            LifecycleStatus.MIGRATED,
            "migrate",
            "actor",
            "ledger",
            predecessor_event_ref="missing",
        )
    ]
    view, result = StatusFold().fold("obj", events)
    assert not result.passed
    assert view.status == LifecycleStatus.UNKNOWN


def test_jvalid_checks_digest_and_result() -> None:
    context = UseContext(
        subject_ref=_ref("subject"),
        subject_pointer="",
        resolved_input_ref=_ref("input"),
        scope=("scope",),
        action="local_use",
        ledger_ref="ledger",
        policy_id="policy",
        schema_version="1",
        digest_algorithm_id="sha256",
        canonical_input_ref=_ref("input"),
        input_digest=Digest("sha256", "abc"),
        freshness_horizon="now",
        resource_bounds=(),
        clock_context="logical",
    )
    record = JudgmentRecord(
        judgment_id="j1",
        judgment_kind="AcceptCarrier",
        subject=_ref("subject"),
        checker_or_policy_ref="checker",
        contract_version="1",
        schema_version="1",
        object_id="j1",
        canonical_digest=Digest("sha256", "abc"),
        use_context_ref="u1",
        canonical_input_ref=_ref("input"),
        input_pointer="",
        input_digest=Digest("sha256", "abc"),
        digest_algorithm_id="sha256",
        result="pass",
    )
    contract = JudgmentContract(
        "AcceptCarrier",
        "carrier",
        "digest",
        "checker",
        "pass_fail_residualize",
        version="1",
    )
    assert jvalid(record, context, contract).passed
