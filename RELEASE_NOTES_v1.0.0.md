# verification-ecology-kit v1.0.0

`verification-ecology-kit` is a Python toolkit for making verification work
clear, traceable, and reviewable.

Use it when you need to record what was checked, what evidence was used, what
is still unresolved, and whether a result is allowed to be reused, shared, or
deployed.

This release is the first stable OSS implementation of the operational parts of
Verifier Ecology Theory.

## Install

```bash
pip install verification-ecology-kit
```

Check the command line tool:

```bash
vek doctor
```

## What Is Included

- Typed Python models for verifier packets, residuals, ledgers, authority
  decisions, certification records, lifecycle status, reachability evidence,
  conformance reports, audits, and runtime reports.
- JSON Schema Draft 2020-12 files for the public records.
- Deterministic JSON canonicalization and SHA-256 digest checks.
- A `vek` command line tool for validation, digesting, bundle conformance,
  reference checks, ledger replay, packet operations, audits, runtime runs, and
  repository scans.
- Audit engines for packet ecology, residual metabolism, aperture regression,
  adversarial ingress, schema overclosure, verifier monoculture, security, and
  local information leaks.
- Runnable examples and documentation written for first-time readers.
- Release gates for linting, typing, tests, schema validation, documentation,
  security scanning, package-content scanning, and wheel install smoke testing.

## What This Release Does Not Claim

This package is not a theorem prover. It does not claim that software can prove
every mathematical statement in the paper.

The package implements the checkable operational parts: structured records,
validators, audits, deterministic reports, residual ledgers, and release gates.
It keeps limits and unresolved work visible instead of hiding them behind a
single pass/fail label.

## Quick Example

```bash
vek packet create --template operational
vek schema list
vek digest object.json
vek conformance bundle.json --profile core --format markdown
```

## Verification Status

The v1.0.0 local release gate passed before publication:

- 76 tests passed.
- Coverage reached 92.22% with a 92% minimum threshold.
- Ruff formatting, Ruff lint, and mypy passed.
- JSON schemas passed metaschema validation.
- MkDocs built in strict mode.
- Secret scan, local-information scan, Bandit, pip-audit, and zizmor passed.
- Wheel and source distribution were built.
- Package-content audit passed.
- Clean wheel install smoke test imported version `1.0.0`.
- The theory-to-code coverage fixture maps the paper glossary to implemented
  modules, schemas, tests, and docs.

## Documentation

Start with the README, then read:

- `docs/quickstart.md`
- `docs/concepts.md`
- `docs/cli.md`
- `docs/conformance.md`
- `docs/audits.md`
- `docs/v1_audit.md`
- `docs/release_readiness.md`

## Citation

Takahashi, K. (2026). *Verifier Ecology Theory: Packetized
Self-Verification Under Residual Accountability*. Zenodo.
https://doi.org/10.5281/zenodo.21147093
