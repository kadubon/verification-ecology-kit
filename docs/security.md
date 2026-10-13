# Security Model

Security defaults are conservative:

- No telemetry.
- No runtime network calls by default.
- No pickle for untrusted data.
- JSON input by default.
- Explicit path handling.
- Secret and local information scanners.
- Package-content verification before publish.

Authority decisions are deny-by-default and block allow decisions when required support is stale, revoked, migrated without accepted witness, unknown, out of scope, reference-broken, digest-mismatched, counterexample-challenged, or blocked by residual gates.

## Experimental capacity profile

See [capacity semantics](capacity.md), [capacity formal boundary](capacity_formal.md),
[interchange](capacity_interchange.md), and [release evidence](capacity_release.md).
This additive profile does not broaden the established VET-Core formal claim.
