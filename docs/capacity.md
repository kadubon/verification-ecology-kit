# Experimental verification capacity

The opt-in capacity profile selects and accounts for finite verification work. It is
experimental and conditional on a registered model. The established Production/Stable
metadata does not establish production assurance for this new profile.

`RuntimeEngine.capacity(contract)` returns `CapacityRuntime` using the same ecology
storage port, history and residual ledger. `RuntimeEngine.run_once()` and the default
quarantine policy retain their previous behavior. No capacity operation runs an
external tool, changes an authority decision, or discharges a source residual.

## Exact finite semantics

A contract registers at most 12 work items/actions, 16 services, eight typed resource
coordinates, eight joint scenarios, 16 integer slots, 1,024 events and 100,000 candidate
evaluations. Numeric coordinates are bounded nonnegative integers; slot seconds is an
explicit positive rational string. One work item is one indivisible registered check.
Fractional completion, preemption, asynchronous scheduling and continuous time are
unsupported and rejected. A job beginning at slot `t` occupies every slot in
`[t, t + duration)`; its output is unavailable until the ending boundary.

Pool capacity is reusable by slot. Consumable budgets are charged once per attempt.
Pool consumption is recorded in pool-slot units, separately from budget coordinates.
Resources have registered identity, kind and unit; their costs are never converted into
a common money/time/risk scalar. A plan reserves full declared costs conservatively on
every branch, including contingent work. An admitted result reports actual costs no
greater than that reservation and releases the unused amount.

Work identity binds source residual, subject and input digests, check and rule version.
Repeated IDs or identical registered checks under different IDs are rejected. Distinct
rechecks require explicit distinct content/version registration. Work and source
residuals are different coordinates: completing a check does not settle its claim.

## Service eligibility and separation

Each service declares domain, supported checks, interface/version, validity boundary,
support references, exposure factors and assumptions. Scheduling checks all of these
against registered work. Exposures should include model/provider, lineage, evaluation
sources, infrastructure, communication and checker derivation as applicable. Declared
separation requires known, nonempty, disjoint exposure sets; different wrapper names
or keys cannot satisfy it. This enforces a finite relation, not statistical independence.

The local profile admits only synthetic or declared-model accounting. It fails closed
for caller-labeled observed records: authenticated operational observation admission
needs a host adapter and is unsupported by this local profile. `observed_service` and
`service_guaranteed_lower_envelope` remain null. A local descriptive completion rate is
labeled synthetic/model accounting and never exported as a guaranteed future rate.

## Allocation objective and uncertainty

The exact selector enumerates omission or every in-horizon start for each registered
action. Applicability, shared capacity, budget, predecessor, validity and separation
checks precede ranking. Its registered lexicographic score is:

1. Minimum protected, on-time check completions over declared joint scenarios.
2. Minimum normalized complete required bundles across domains/scenarios.
3. Required completed-work age credit, then fewer missed required deadlines.
4. Lower costs in declared resource-coordinate order, then stable action/start IDs.

Bundles count once. Optional construction/calibration work cannot improve required
bundle coverage. Qualified negative verdicts earn the same completion credit as
positive verdicts. Remaining repair obligations are reported separately so sound
negative checking is not penalized merely for its sign.

The schedule is nonadaptive; no hidden scenario ID is an input to selection. Each
declared joint outcome vector is expanded separately. A failed success prerequisite
stops dependent work; explicit cancellation releases only a provably unstarted
reservation. A negative prerequisite can enable a registered repair action. A safe
partial schedule is not a claim that every branch completes all protected work.

The independent checker reconstructs occupancy, budgets, dependencies, separation,
all branch completions and objective values. It never imports the selector or trusts
its score. Search counters describe selector execution; schedule checking alone does
not prove that a third-party claim of exhaustive search is authentic. Complete search
means optimum only over the declared catalogue. A budget interruption reports unknown
with a checked incumbent, never infeasibility. FIFO, earliest-deadline and catalogue
order comparisons use the same constraints and budget. A separately implemented tiny
exhaustive oracle checks matched finite instances in property tests.

## Explicit work-state changes

Plan/inspect/compare/export are read-only. `apply-local` explicitly records reservations;
it does not dispatch work. Event kinds are `apply`, `tick`, `dispatch`, `result`, `cancel`
and `withdraw`. Dispatch records host-supplied work state; it does not invoke tools.
Unknown dispatched work retains reservations until reconciliation. Passing time does
not credit completion; an overdue unknown dispatch conservatively holds its pool for
the rest of the finite horizon. Cancellation removes an unstarted attempt while
preserving the unfinished source work.

Results bind request, contract, scope, subject/input digests, service/version/interface,
attempt, time interval, actual costs, outcome and support references. Existing VEK core
conformance checks also inspect the admitted result envelope. This is structural local
evidence, not operator authentication. Positive and negative qualified results complete
one check; timeout, invalid and inconclusive results complete none. Negative checks add
a separate repair residual. A registered positive repair can clear the local repair
queue coordinate; the historical failure and epistemic residual remain visible pending
their normal disposition process.

Result and event retries are idempotent; conflicting duplicates fail. Snapshots are
replayed from the bounded event history. They cannot reset consumption or queues.
Follow-up packets use the existing generator and accountability hooks, deduplicated
by source/content/rule/check. Follow-up generation never credits extra service or
discharges the source residual. The capacity state is archived alongside existing
ecology state. A changed contract requires a distinct namespace, not overwriting history.

`JsonStore` writes a temporary whole-state file then atomically replaces its target.
The host must serialize one writer across load/check/save. This is neither a durable
distributed transaction nor cross-process reservation safety. Failed replacement
leaves the previous state; in-memory admission copies caller payloads before storing.
In CCR mode VEK exports proposals against CCR revisions/pools; CCR owns atomic admission.

## Paid development, revalidation and queue diagnostics

The investment example reserves construction, calibration, a declared separate
counter-check and activation before later verification. Activation only enables a
registered model option. It creates no observed capacity or executable checker code.
The old service remains a catalogue fallback. Overpriced investment loses to a simple
baseline; missing independent support cannot be upgraded by self-testing. No generated
Python, package installation or provider call is part of these actions.

The expiry control rejects expired evidence. The revalidation example pays for a
separate calibration step before selecting a predeclared renewed model service; it
does not erase the old service or turn calibration into external measurement.

Branch traces report backlog by boundary, peak backlog, unfinished checks, missed
deadlines, complete bundles, repair and costs. The burst/outage example misses a
deadline despite spare capacity elsewhere. These are finite conditional diagnostics,
not infinite-horizon queue-stability or empirical acceleration claims.

## CLI and Python

```text
vek capacity example investment
vek capacity example negative
vek capacity example integrated
vek capacity inspect contract.json --store ecology.json
vek capacity plan contract.json --store ecology.json
vek capacity check-plan contract.json --store ecology.json --plan plan.json
vek capacity apply-local contract.json --store ecology.json --plan plan.json --event-id apply-1
vek capacity ingest contract.json --store ecology.json --event event.json
vek capacity replay contract.json --store ecology.json
vek capacity compare contract.json --store ecology.json
vek capacity export contract.json --store ecology.json --format vek
```

Python equivalents are `Contract.from_dict`, `CapacityRuntime.inspect/plan/update/event`,
`check_plan`, `compare`, `capacity_report`, `ccr_proposals` and `cait_envelope` in the
`verification_ecology_kit.capacity` modules. Contract source residuals must already
exist in the ecology store; inert examples construct a synthetic namespace explicitly.
`capacity.examples.scenario(name)` returns its contract and starting ecology.

Exit codes: 0 for a valid operation/feasible plan, 2 for invalid input, 3 for incomplete
search with protected feasibility unknown, 4 for complete finite protected infeasibility.
A valid checked partial schedule may be returned with explicit unmet protected work.
The base wheel includes schemas, finite examples and the pinned CCR schema, and runs
offline outside the checkout with `python -m verification_ecology_kit.capacity.installed_check`.

See [interchange](capacity_interchange.md), [formal boundary](capacity_formal.md), and
[requirement matrix](capacity_requirements.md).
