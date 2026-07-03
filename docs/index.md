# verification-ecology-kit

This package turns Verifier Ecology Theory into executable records, checks, and
a bounded formal VET-Core semantics. It focuses on what software can evaluate:
packet completeness, residual accounting, reference integrity, digest stability,
lifecycle status, authority gates, audit reports, and formal trace
conformance.

verification-ecology-kit provides a complete formal operational semantics for the VET-Core implemented by this package, with machine-checked safety theorems and Python conformance tests against the formal semantics.

The Python implementation is conformance-tested against the formal VET-Core
semantics. It is not fully formally verified.

Start with [Quickstart](quickstart.md), then use [Concepts](concepts.md) for the
plain-language model. Release reviewers should read [V1 Audit](v1_audit.md) and
[Formal Claims](formal_claims.md), [Semantic Boundary](semantic_boundary.md),
and [Release Readiness](release_readiness.md) before tagging or publishing.
