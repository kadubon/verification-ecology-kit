# Changelog

## 1.1.0

- Added executable semantic readiness gates for operational empty bundles, strict JSON Pointer indices, authority denial paths, packet operation admissibility, runtime reporting, and scanner redaction.
- Added reconstructed `JValid` checks, support-aware authority resolution, and support reference blocking for stale, migrated, redacted, or residual-gated evidence.
- Added replayable residual ledger event payloads, residual metabolism route classes, and tamper detection for ledger event digests.
- Added structured runtime stages, schema-overclosure checks, reachability-certificate calls, aperture/frontier comparisons, and packet ecological invariant checks.
- Moved runtime JSON loading to stable model serde helpers and added atomic save with symlink guards.
- Clarified README and v1 audit documentation around the semantic completeness boundary.
- Expanded verifier packet schemas and loaders for lineage, anti-overclosure, ecological invariants, residual liveness, circulation residuals, and inherited boundary metadata.
- Hardened conformance, authority, packet operation, runtime, residual ledger, and reference resolution behavior against silent support loss.
- Added TOML allowlist support and broader token detection for local secret scanning.
- Updated CI and release documentation to use locked dependency sync.

## 1.0.0

- Stabilized the package metadata and public version for the first stable OSS release.
- Made `vek packet operate` consume real packet JSON inputs and write output packets to `--out`.
- Made audit commands consume explicit input files instead of internal sample packets.
- Added JSON loaders for packets, residual ledgers, bundles, references, and runtime state.
- Deepened operational conformance checks for lifecycle status, judgment validity, residual liveness, and deny-by-default authority decisions.
- Improved JSON runtime persistence so saved ecology state loads back into packet population, history, residual ledger, archive, and reusable capital.
- Raised the test coverage gate to 92% and added focused tests for CLI JSON boundaries.
- Added v1 readiness and release-gate documentation plus `scripts/check_v1_readiness.py`.
- Expanded README navigation and first-time-user explanations.

## 0.1.0

- Initial implementation of packet models, residual ledgers, canonicalization, digests, references, conformance reports, audits, runtime loop, CLI, schemas, tests, and PyPI publishing preparation.
