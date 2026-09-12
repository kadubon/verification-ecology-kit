"""Separately implemented tiny exhaustive oracle under matched constraints/budgets."""

from dataclasses import replace
from itertools import product

from hypothesis import given, settings
from hypothesis import strategies as st

from verification_ecology_kit.capacity.checker import Snapshot
from verification_ecology_kit.capacity.examples import scenario
from verification_ecology_kit.capacity.selector import plan


@settings(max_examples=30, deadline=None)
@given(
    capacity=st.lists(st.integers(0, 2), min_size=3, max_size=3),
    budget=st.integers(0, 3),
    negative=st.booleans(),
)
def test_tiny_oracle(capacity, budget, negative):
    c, _ = scenario("protected")
    c = replace(
        c,
        resources=(
            replace(c.resources[0], capacity=tuple(capacity)),
            replace(c.resources[1], capacity=(budget,)),
        ),
        scenarios=(
            replace(c.scenarios[0], outcomes=("negative" if negative else "positive",) * 3),
        ),
    )
    # Independent enumeration: no production checker, model reducer, cached scores,
    # or selector helper. One unit per job and one bundle per domain obligation.
    oracle = None
    for slots in product((-1, 0, 1, 2), repeat=3):
        used = sum(t >= 0 for t in slots)
        if used > budget or any(
            sum(t == slot for t in slots) > capacity[slot] for slot in range(3)
        ):
            continue
        protected = int(slots[2] == 0)
        age = 3 * used
        missed = sum(t < 0 or t + 1 > c.work[i].deadline for i, t in enumerate(slots))
        score = (protected, used / 3, age, -missed, -used, -used)
        if oracle is None or score > oracle:
            oracle = score
    selected = plan(c, Snapshot(spent=[0, 0]))
    from fractions import Fraction

    actual = tuple(float(Fraction(x)) for x in selected["checked"]["objective"])
    assert actual == oracle
    assert selected["search"]["complete"]
