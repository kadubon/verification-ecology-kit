# Semantic Boundary

This page separates the formal VET-Core claim from implementation checks and
from theory that remains outside this package.

## Formalized Syntax

The Lean syntax layer covers:

- identifiers, references, digests, statuses, visibility, trust status
- residual kinds and routes
- residual ledgers and ledger events
- verifier packets, counter-packets, boundary records, reachability
  certificates, counterexample channels, certification records, auth inputs,
  authority records, aperture records, frontier records, ecology states, and
  runtime traces
- the packet-operation and runtime-stage names implemented by Python

## Formalized Static Semantics

Lean predicates define well-formed residuals, ledgers, packets, authority
records, support eligibility, local sovereignty, schema revisability, aperture
accounting, and ecology-wide invariants.

## Formalized Operational Semantics

Lean defines small-step packet-operation semantics for:

- `fork`
- `specialize`
- `generalize`
- `compose`
- `contrast`
- `repair`
- `retire`
- `quarantine`
- `internalize`
- `redact`

It also defines runtime-stage semantics corresponding to the Python
`RuntimeEngine` report stages.

## Machine-Checked Theorems

The theorem list is maintained in [formal_claims.md](formal_claims.md) and in
`formal/lean/VETCore/Theorems.lean`.

## Python Conformance Tests

Python implementation is conformance-tested against the formal VET-Core
semantics through `verification_ecology_kit.formal_bridge`, golden formal
traces, and `tests/formal`.

The Python implementation is not fully formally verified. The repository does
not contain a Python-to-Lean refinement proof or verified Python extraction
path.

## Not Formalized

The following remain outside the formal claim:

- all statements in the full Verifier Ecology Theory paper that are broader
  than VET-Core;
- arbitrary user-defined verifier code;
- all possible external tool behavior;
- empirical adequacy of a checker in a domain;
- security of third-party dependencies;
- correctness of future schemas that are not mapped through the formal
  coverage gate.

These items must be handled by ordinary tests, review, audit, security gates,
or residual obligations.
