# Formal Claims

verification-ecology-kit provides a complete formal operational semantics for the VET-Core implemented by this package, with machine-checked safety theorems and Python conformance tests against the formal semantics.

This is the exact v1.2.0 formal claim. It is allowed only when all formal gates
pass:

```bash
cd formal/lean
lake build
uv run python scripts/check_formal_coverage.py
uv run python scripts/check_formal_claims.py
uv run pytest tests/formal
```

## What Is Claimed

- VET-Core syntax is formalized in Lean.
- VET-Core static semantics are formalized in Lean.
- VET-Core small-step packet-operation semantics are formalized in Lean.
- VET-Core runtime-stage semantics are formalized in Lean.
- Ecological invariants are formalized in Lean.
- The listed safety theorems are machine-checked.
- Python operation and runtime traces are conformance-tested against the formal
  VET-Core contract.

## What Is Not Claimed

- The project does not prove all of Verifier Ecology Theory.
- The project does not prove AI safety.
- The project does not prove correctness for every verifier in every setting.
- The project does not provide a verified extraction path from Lean to Python.
- The project does not claim that arbitrary Python execution follows from the
  Lean proof without testing.

Python implementation is conformance-tested against the formal VET-Core
semantics and is not fully formally verified.

## Theorem Set

The v1.2.0 release contains these Lean theorems:

| Claim area | Lean theorem |
| --- | --- |
| Residual preservation | `residual_preservation_step` |
| Blocking residual authority gate | `active_residual_without_live_route_blocks_authority` |
| Operation invariant accounting | `admissible_operation_preserves_or_residualizes_invariants` |
| Composition certification boundary | `compose_not_automatically_certified` |
| Redaction accountability | `redaction_requires_residual` |
| Generalization boundary work | `generalization_requires_boundary_work` |
| Authority support eligibility | `authority_allow_requires_support_eligibility` |
| Stale, revoked, or unknown support | `stale_revoked_unknown_support_blocks_authority` |
| Migrated support witness | `migrated_support_requires_witness` |
| External packet authority boundary | `external_packet_not_authority_before_internalization` |
| Runtime ecology preservation | `runtime_preserves_ecological_invariants` |
| Packet spam boundary | `packet_spam_not_acceleration` |
| Aperture debt | `aperture_loss_requires_debt` |
| Schema-field residualization | `missing_schema_field_can_residualize` |
| Schema revisability | `anti_overclosure_overclosure_blocked` |

No theorem in this v1.2.0 set is weakened or deferred.

## Claim Control

The script `scripts/check_formal_claims.py` checks:

- required formal files exist;
- Lean source does not contain blocked proof tokens;
- required theorem names exist;
- README and formal docs carry the exact allowed claim;
- docs distinguish Python conformance testing from full formal verification;
- forbidden broad claims do not appear.
