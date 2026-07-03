from __future__ import annotations

from datetime import UTC, datetime, timedelta

from verification_ecology_kit.model.history import ObservableProcessHistory
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.records import LedgerStatus, ResidualKind
from verification_ecology_kit.model.residuals import (
    ResidualRecord,
    ResidualRoute,
    check_residual_liveness,
)


def test_history_prefix_is_append_only() -> None:
    first = ObservableProcessHistory()
    first.append("observation", {"x": 1})
    second = ObservableProcessHistory(events=list(first.events))
    second.append("action", {"y": 2})
    assert first.is_prefix_of(second)
    assert not second.is_prefix_of(first)


def test_ledger_operations_preserve_trace() -> None:
    ledger = ResidualLedger()
    residual = ResidualRecord(
        kind=ResidualKind.UNRESOLVED,
        origin="o",
        scope=("s",),
        obligation="inspect",
    )
    add_event = ledger.add(residual)
    merged = ResidualRecord(
        kind=ResidualKind.UNRESOLVED,
        origin="o",
        scope=("s",),
        obligation="merged",
    )
    ledger.merge((residual.residual_id,), merged)
    ledger.retire(merged.residual_id, justification="done")
    assert add_event.kind == "add"
    assert ledger.residuals[residual.residual_id].status == LedgerStatus.MERGED
    assert ledger.residuals[merged.residual_id].status == LedgerStatus.RETIRED
    assert ledger.trace_ok().passed


def test_quarantine_and_redact_create_visible_residual() -> None:
    ledger = ResidualLedger()
    residual = ResidualRecord(ResidualKind.UNTRANSLATED, "o", ("scope",), "translate")
    ledger.add(residual)
    ledger.quarantine(residual.residual_id, reason="low trust")
    redaction, _ = ledger.redact(residual.residual_id, reason="privacy")
    assert ledger.residuals[residual.residual_id].status == LedgerStatus.REDACTED
    assert redaction.kind == ResidualKind.REDACTION_RESIDUAL


def test_residual_liveness_requires_route() -> None:
    no_route = ResidualRecord(ResidualKind.UNRESOLVED, "o", ("s",), "route")
    assert not check_residual_liveness(no_route).passed
    deadline = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    routed = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "o",
        ("s",),
        "route",
        route=ResidualRoute("owner", deadline, ("1h",), "daily"),
    )
    assert check_residual_liveness(routed).passed
