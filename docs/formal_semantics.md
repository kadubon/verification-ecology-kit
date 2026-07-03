# Formal Semantics

verification-ecology-kit provides a complete formal operational semantics for the VET-Core implemented by this package, with machine-checked safety theorems and Python conformance tests against the formal semantics.

The claim is scoped to VET-Core, the bounded language implemented by this
package. It is not a claim about every possible verifier ecology or every
statement in Verifier Ecology Theory.

## VET-Core Scope

VET-Core includes:

- object identifiers, object references, and digest records
- lifecycle statuses
- residual kinds, residual routes, residual ledgers, and ledger events
- verifier packets and counter-packets
- boundary records and reachability certificates
- counterexample channels and sound-gap residuals
- certification records
- authority decisions and auth inputs
- aperture and frontier profiles
- packet operations: `fork`, `specialize`, `generalize`, `compose`,
  `contrast`, `repair`, `retire`, `quarantine`, `internalize`, and `redact`
- runtime stages: candidate generation, core accountability, semantic
  accountability, residual metabolism, packet generation, boundary and
  reachability checks, counter-packet checks, schema-overclosure checks,
  lineage checks, authority checks, quarantine and internalization decisions,
  repair and retirement decisions, aperture updates, and frontier updates

The Lean source for these objects is in `formal/lean/VETCore/Syntax.lean`.

## Static Semantics

`formal/lean/VETCore/WellFormed.lean` defines the static predicates used by
the VET-Core release claim:

- `WellFormedResidual`
- `LiveResidual`
- `ResidualClassLive`
- `WellFormedLedger`
- `TraceOK`
- `WellFormedPacketCore`
- `CoreAccountablePacket`
- `HasCounterPacketOrResidual`
- `BoundaryPreserved`
- `OriginTraceable`
- `ScopeAccountable`
- `ResidualPreserved`
- `RetirementLive`
- `ApertureAccounted`
- `SchemaRevisable`
- `LocalSovereigntySatisfied`
- `WellFormedPacket`
- `WellFormedAuthority`
- `WellFormedEcologyState`
- `EcologyInvariantHolds`

The ecological invariant predicate requires origin traceability, accounted
scope expansion, residual preservation, boundary preservation, counter-packet
availability, retirement liveness, aperture accounting, and schema
revisability.

## Operational Semantics

`formal/lean/VETCore/Semantics.lean` defines:

- `Step : EcologyState -> PacketOperation -> EcologyState -> Prop`
- one constructor for each packet operation
- a `StepCertificate` that records preconditions, packet changes, residual
  additions, ledger events, boundary consequences, authority consequences,
  aperture consequences, lineage consequences, residual accounting, and
  invariant accounting

Important rules encoded by the constructors:

- `compose` requires a fresh boundary obligation and a fresh counter-packet
  obligation.
- `generalize` requires boundary work or an `unexcluded` residual.
- `redact` requires a redaction residual.
- `repair` requires a residual disposition witness.
- `retire` requires a retirement witness and reinspection condition.
- `quarantine` requires a quarantine witness.
- `internalize` requires an external-internalization witness with local trust,
  boundary work, local counter hook, and translation residual handling.

## Runtime Semantics

`formal/lean/VETCore/Runtime.lean` defines:

- `RuntimeStep : EcologyState -> RuntimeStage -> EcologyState -> Prop`
- one constructor for each Python runtime stage
- a `RuntimeCertificate` that records checker results and state deltas

Runtime transitions preserve `EcologyInvariantHolds` or residualize every
violation with a live residual route.

## Machine-Checked Theorems

The machine-checked theorem set is in
`formal/lean/VETCore/Theorems.lean`:

- `residual_preservation_step`
- `active_residual_without_live_route_blocks_authority`
- `admissible_operation_preserves_or_residualizes_invariants`
- `compose_not_automatically_certified`
- `redaction_requires_residual`
- `generalization_requires_boundary_work`
- `authority_allow_requires_support_eligibility`
- `stale_revoked_unknown_support_blocks_authority`
- `migrated_support_requires_witness`
- `external_packet_not_authority_before_internalization`
- `runtime_preserves_ecological_invariants`
- `packet_spam_not_acceleration`
- `aperture_loss_requires_debt`
- `missing_schema_field_can_residualize`
- `anti_overclosure_overclosure_blocked`

The release gate requires `lake build` to compile these files with no blocked
proof tokens.

## Python Conformance

Python operation reports are exported through
`verification_ecology_kit.formal_bridge` into formal trace JSON:

- `before_state`
- `operation`
- `after_state`
- residual deltas
- boundary deltas
- authority deltas
- aperture and frontier deltas
- invariant checks

The schemas are:

- `formal-trace.schema.json`
- `formal-stage.schema.json`
- `formal-semantics-report.schema.json`

Python implementation is conformance-tested against the formal VET-Core
semantics. The project does not claim a refinement proof from Python code to
Lean, nor a verified extraction path.

## Optional TLA+ Model

`formal/tla/VETRuntime.tla` models small finite-state liveness scenarios for
residual routing and quarantine before internalization. It is useful review
material, but the release-blocking proof gate is Lean plus the Python formal
coverage and claim checks.
