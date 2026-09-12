# Changelog

## 1.3.0

- Add experimental opt-in finite verification-capacity contracts, typed shared pools
  and budgets, bounded exact allocation, independent schedule checking and joint
  synthetic/model outcomes. Existing runtime defaults and encodings are unchanged.
- Integrate explicit work/reservation/result replay with ecology storage, core evidence
  conformance, deduplicated follow-ups and preserved negative/repair residuals.
- Add paid model-only verifier development, repair/revalidation and adverse queue
  examples, versioned capacity reports and pinned CCR proposals/partial CAIT envelopes.
- Add a separate Lean resource-accounting core, Python conformance and six bounded
  fault-injection controls. Make Lean build targets explicit and repair previously
  uncompiled VET-Core proof scripts without changing theorem statements or predicates.
- Publish tested artifacts by download and SHA-256 verification, eliminating the
  publisher rebuild. Add offline installed-wheel checks on Windows/macOS and Linux.
- No external empirical acceleration experiment was performed. Scheduling or local
  checking does not establish scientific truth, independence, capacity growth or authority.

## 1.2.0

- Added a Lean 4 VET-Core formalization covering syntax, static semantics,
  packet-operation semantics, runtime-stage semantics, ecological invariants,
  authority rules, aperture rules, residual accounting, and safety theorems.
- Added formal claim and semantic-boundary documentation that limits the formal
  claim to VET-Core and states that Python is conformance-tested rather than
  fully formally verified.
- Added formal trace schemas, `verification_ecology_kit.formal_bridge`, golden
  formal coverage, and formal Python conformance tests.
- Added `scripts/check_formal_coverage.py` and `scripts/check_formal_claims.py`
  to block overstated release claims.
- Updated readiness, release gates, CI, README, and package metadata for the
  v1.2.0 formal VET-Core release.

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
