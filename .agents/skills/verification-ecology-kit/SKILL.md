---
name: verification-ecology-kit
description: "Create, inspect, and audit structured verification evidence with Verifier Ecology Kit: verifier packets, evidence bundles, residual ledgers, provenance/digest checks, conformance, verifier independence, and evidence authority. Use when the primary object is an evidence record or verification decision with unresolved obligations. Do not use for generic unit tests, linting, code review, generic formal methods, or claims that arbitrary software is correct."
license: Apache-2.0
metadata:
  author: K. Takahashi
  repository: https://github.com/kadubon/verification-ecology-kit
  version: "1.0"
---

# Verification Ecology Kit

Treat valid structure as reviewable evidence, not proof of the represented claim.

## Fast path

1. Identify the verification object: packet, bundle, ledger, schema, or audit input.
2. Preserve stated unknowns and unresolved obligations; do not replace them with zero or closed.
3. Run `vek doctor`, then use the smallest applicable check.
4. Validate schema, digest, and references before interpreting conformance.
5. Run a targeted audit only when its input and question match.
6. Report supported evidence, residuals, authority scope, and non-claims separately.

## When to use

Use for verifier packets, evidence bundles, digest/provenance checks, residual work,
conformance audits, verifier monoculture, stale evidence, or evidence-reuse authority.
For persistent or retrieved agent memory, use Certified Memory Governance Layer. For
adaptive scientific inference, use Audit-Closed AI Scientist. For general agent-output
admission, use Percolation Inversion Compiler. For trust-fixture evaluation, use ATRB.

## Do not use

- Generic tests, linting, source review, or a broad correctness claim without an evidence record.
- As a substitute for an independent verifier, a factual investigation, or deployment approval.
- To treat syntactically valid JSON, an `allow` record, or core-profile conformance as universal authorization.

## Workflow

Start with the current command surface:

```text
uv run vek doctor
uv run vek validate OBJECT.json --schema SCHEMA --profile core
uv run vek digest OBJECT.json
uv run vek refs check BUNDLE.json
uv run vek conformance BUNDLE.json --profile core --format json
```

Use `--profile operational` only when lifecycle, judgment, trace, counterexample,
soundness-gap, and authority checks are relevant. Use `--profile federated` only for
external packet translation or cross-ecology work. For a packet-specific question use
`vek audit packet-ecology PACKET_OR_BUNDLE.json`; for a population-independence question
use `vek audit monoculture PACKETS_OR_BUNDLE.json`. Read
[workflow map](references/workflow-map.md) before selecting an audit.

Do not mutate packet files unless the user asked for a packet operation. If requested,
use `vek packet operate ... --out OUTPUT.json`, retain the input, and inspect the emitted
residual references.

## Evidence and result semantics

For finite verification workload allocation, explicitly select `vek capacity` or
`RuntimeEngine.capacity(contract)`. Read `docs/capacity.md` before applying a local
plan. Inspect/plan/check/compare/export are read-only; apply-local and ingest change
only the serialized local work ledger. Preserve unknown dispatches and negative
results. Investment enables model-only options, never observed service or authority.
Use `capacity-report.schema.json`; CCR owns proposal admission and CAIT owns growth
accounting. Existing runtime defaults and VET-Core theorem statements remain intact.

Schema, digest, and reference checks establish only their named mechanical properties.
Core conformance can be structurally valid while operational authority remains blocked.
`allow` is deny-by-default scoped authorization only when its required support is current;
it is not a universal action grant. Read [claim boundary](references/claim-boundary.md)
when reporting support or authority.

## Retrieve only what is needed

- Read `docs/cli.md` for flags and all command variants.
- Read `docs/conformance.md` for profile-specific checks and status rules.
- Read [workflow map](references/workflow-map.md) for command selection.
- Read [claim boundary](references/claim-boundary.md) only for formal interpretation or authority/reuse decisions.

## Validate

Run the exact check used on the submitted input and, for repository changes, run:

```text
uv run pytest
uv run ruff check .
```

## Report

State: Outcome; evidence and checks run; remaining residuals/unknowns; authority and
scope; non-claims; and the next smallest warranted action. Distinguish `validated`,
`supported`, `authorized`, and `settled`.

## Required non-claims

- VET-Core implementation is narrower than all Verifier Ecology Theory.
- Valid JSON, a matching digest, or a passing conformance report does not prove truth.
- No unresolved residual becomes closed merely because another check passed.
