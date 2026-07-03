# Formal Claims

verification-ecology-kit provides a complete formal operational semantics for
the VET-Core implemented by this package, with machine-checked safety theorems
and Python conformance tests against the formal semantics.

This claim is limited to the VET-Core language defined in
`formal/lean/VETCore`. It covers:

- complete formal syntax for the implemented core records and transitions;
- formal static semantics for well-formed packets, residual ledgers, authority
  inputs, support eligibility, aperture accounting, and schema revisability;
- small-step operational semantics for packet operations;
- runtime-stage transition semantics for the Python runtime report stages;
- ecological invariant predicates;
- machine-checked safety theorems in Lean;
- Python trace and operation conformance tests against the formal names and
  required obligations.

It does not claim a proof of all Verifier Ecology Theory, full formal
verification of arbitrary Python execution, AGI safety, universal verifier
correctness, or a verified Python extraction path.
