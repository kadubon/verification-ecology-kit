from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.digest import DigestPolicy
from verification_ecology_kit.model.authority import AuthorityEngine
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.lifecycle import StatusEvent, StatusFold
from verification_ecology_kit.model.records import (
    AuthorityAction,
    AuthorityDecisionValue,
    LifecycleStatus,
    ResidualKind,
)
from verification_ecology_kit.model.residuals import ResidualRecord

json_scalars = st.one_of(
    st.none(), st.booleans(), st.integers(min_value=-1000, max_value=1000), st.text()
)
json_values = st.recursive(
    json_scalars,
    lambda children: (
        st.lists(children, max_size=4)
        | st.dictionaries(st.text(min_size=1, max_size=6), children, max_size=4)
    ),
    max_leaves=10,
)


@given(json_values)
def test_digest_stability(value: object) -> None:
    policy = DigestPolicy()
    canonicalizer = Canonicalizer()
    assert policy.digest_json(value, canonicalizer=canonicalizer) == policy.digest_json(
        value,
        canonicalizer=canonicalizer,
    )


@given(st.lists(st.text(min_size=1, max_size=8), min_size=1, max_size=5))
def test_ledger_add_preserves_residual_count(names: list[str]) -> None:
    ledger = ResidualLedger()
    for name in names:
        ledger.add(ResidualRecord(ResidualKind.UNRESOLVED, name, ("scope",), "obligation"))
    assert len(ledger.residuals) == len(names)
    assert ledger.trace_ok().passed


@given(st.sampled_from(list(LifecycleStatus)))
def test_status_fold_returns_declared_status(status: LifecycleStatus) -> None:
    event = StatusEvent("obj", LifecycleStatus.UNKNOWN, status, "cause", "actor", "ledger")
    view, _ = StatusFold().fold("obj", [event])
    if status == LifecycleStatus.MIGRATED:
        assert view.status == LifecycleStatus.UNKNOWN
    else:
        assert view.status == status


def test_authority_property_deny_by_default() -> None:
    decision, _ = AuthorityEngine().aggregate(AuthorityAction.DEPLOYMENT, [])
    assert decision == AuthorityDecisionValue.DENY
