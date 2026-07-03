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
