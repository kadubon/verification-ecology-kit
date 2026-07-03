# Optional TLA+ Runtime Model

`VETRuntime.tla` is a small finite-state model for liveness-facing runtime
scenarios:

- residual routes become live before authority is allowed;
- external packets are quarantined before internalization;
- authority is not allowed while residual routing is incomplete.

This model is optional. The release-blocking formal gate is the Lean VET-Core
build plus the Python coverage and claim checks.
