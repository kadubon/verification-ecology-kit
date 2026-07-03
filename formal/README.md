# Formal Semantics

This directory contains the machine-checked VET-Core formalization used by
verification-ecology-kit.

- `formal/lean` defines the VET-Core syntax, static semantics, small-step
  operation relation, runtime stage relation, invariants, authority rules, and
  safety theorems.
- `formal/tla` contains an optional finite-state liveness model for residual
  routing and quarantine scenarios. It is explanatory and is not counted as the
  release-blocking proof gate.

The release gate for the Lean layer is:

```bash
cd formal/lean
lake build
```

The Python package is conformance-tested against this formal VET-Core
semantics. It is not claimed to be fully formally verified.
