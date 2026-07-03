# Examples

The `examples` directory contains:

- Minimal packet creation
- Residual ledger operations
- Operational bundle conformance
- External packet quarantine
- Overclosure audit
- Runtime loop
- Federated bundle conformance
- Authority gate aggregation
- Reachability certificate admissibility
- Schema migration witness

Each example is a regular Python file. Run one with:

```bash
uv run python examples/authority_gate.py
```

The examples are intentionally small. They show the object shape and the
decision or report produced by the library, without requiring network access or
external services.
