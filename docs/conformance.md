# Conformance

The conformance engine runs ordered checks:

1. `SchemaOK`
2. `DigestPolicyOK`
3. `ObjectDigestOK`
4. `BundleDigestOK`
5. `RefGraphOK`
6. `StatusOK`
7. `JudgmentOK`
8. `ResidualOK`
9. `AuthorityOK`

Core profile requires schema, digest, references, bundle digest, and residual accounting. Operational profile adds lifecycle, judgment, trace, counterexample, soundness gap, and authority checks. Federated profile adds external packet translation, migration witnesses, sovereignty gates, redaction residuals, and cross-ecology quarantine.

## Status, Judgment, And Authority

Operational and federated conformance use the following rules:

- `StatusOK` accepts `active` and `migrated` objects. A missing status, broken
  status reference, `stale`, `revoked`, or `unknown` status blocks support.
- `JudgmentOK` accepts judgment records whose `jvalid_result` is `pass` or
  `not_applicable`. Failed, stale, revoked, unknown, or not-yet-checked
  judgments block support.
- `AuthorityOK` treats authority as deny-by-default. `allow` decisions must be
  active or migrated, keep `deny_by_default: true`, and include support
  judgments when support refs are required. `deny`, `quarantine`, and unresolved
  `residualize` decisions do not authorize the action.

Core conformance does not require these higher-level checks. That lets a bundle
be structurally valid while still requiring operational review before use.
