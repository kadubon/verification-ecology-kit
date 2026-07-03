# Changelog

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
