# Capacity formal boundary

The existing VET-Core theorem statements and predicates are preserved. The actual
`lake build` gate now has explicit default library targets and compiles VET-Core's
examples/import closure plus the separate `CapacityCore.Accounting` module. This
exposed existing syntax/proof-script errors hidden by the previous empty default
build; fixes change indentation and Boolean equality elimination, not statements.

The new resource core uses natural-number work/resource coordinates and concrete
guarded `reserve`, `finish`, `releaseUnused`, `followup` and `activateModel` functions.
It proves:

| Property | Theorem |
| --- | --- |
| Available/reserved conservation | `reservation_conserves` |
| Shared allocation bounded by available plus reserved | `shared_pool_bounded` |
| Work and reserved/consumed conservation | `completion_conserves` |
| Natural remaining work | `nonnegative_remaining` |
| Successful fresh completion requires predecessor membership | `no_completion_before_predecessors` |
| Completion preserves authority and source residuals | `completion_preserves_authority_residuals` |
| Duplicate result gives no second credit | `duplicate_result_no_credit` |
| Follow-up preserves source residuals and authority | `followup_preserves_source` |
| Model activation gives no authority | `model_activation_no_authority` |
| Unused reservation release conserves resources | `release_conserves` |
| Reservation cannot credit completion or authority | `reservation_no_completion` |

Python `capacity.formal.trace` projects actual reducer histories into work/resource
coordinates. Its separately implemented numeric evaluator checks conservation,
nonnegativity, monotone accounting and authority non-increase, including negative
trace controls. Pool coordinates project total pool-slot units; the independent
schedule checker additionally enforces each individual slot. Partial actual resource
use decomposes into guarded completion plus release of unused reservation.
`generate_capacity_lean_traces.py` also exports a real negative-result/retry history
into `CapacityCore.Conformance.lean`. Lean decides the concrete reserve, finish and
release equalities for both resource coordinates; CI checks generated-source drift.

The formal result is a subsystem accounting boundary, not a Python-to-Lean refinement
proof. Optimizer optimality, global scheduling, real service rates, real verifier
correctness, statistical independence and queue stability are outside the Lean claim.
Python is conformance-tested, not wholly formally verified. A positive check outcome
is a local accounting label and cannot introduce a VET authority decision.

Run from the repository root:

```text
uv run python scripts/check_formal_coverage.py
uv run python scripts/check_formal_claims.py
uv run pytest tests/formal --no-cov
uv run python scripts/check_capacity_faults.py
```

Then run `lake build` from `formal/lean`. No proof waivers, new axioms or disabled
proof checks are used. Six selected isolated guard-removal faults cover cost bounds,
duplicate results, separation, stale plans, authority and conservation; every selected
fault must produce a test assertion failure, with no infrastructure/collection error.
