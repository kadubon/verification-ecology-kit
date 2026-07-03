# V1 Readiness

This page tracks whether the package is ready to carry the v1 line, including
the current `1.2.0` formal VET-Core release.

The project may contain useful working features before a stable v1 claim. A v1
release requires a stronger claim: the command line interface, Python API,
schemas, audits, examples, security checks, documentation, and semantic
negative gates must all agree with the theory-facing contract.

## Current Release State

Current package version: `1.2.0`

Current readiness decision: **ready for v1.2.0 release artifacts when the
strict gate, formal gate, package gate, docs gate, and security gate pass on
the current worktree**.

The package is usable as a stable OSS implementation with a formal VET-Core
claim. The readiness check is available as:

```bash
uv run python scripts/check_v1_readiness.py
```

Use strict mode before any release candidate:

```bash
uv run python scripts/check_v1_readiness.py --strict
```

## Readiness Matrix

| Area | Required v1 condition | Current status |
| --- | --- | --- |
| Theory mapping | Each software concept maps to a stated theory term or explicitly documented approximation. | Implemented. `docs/theory_mapping.md` gives both theory names and plain-language terms. |
| Schema-first records | Public JSON objects have schemas, examples, and validation paths. | Implemented for the v1 public objects and release schema gate. |
| Canonicalization and digests | Digest checks use deterministic JSON canonicalization and reject mismatches. | Implemented for object, bundle, reference, and report workflows. |
| Reference integrity | Bundle references are resolved with schema, pointer, and digest checks. | Implemented in conformance and reference checking. |
| Lifecycle and authority | Status, judgment, residual, and authority checks affect support decisions. | Implemented for conformance inputs. Status references, judgment validity, and deny-by-default authority decisions now affect operational decisions. |
| Residual ledger | Residual changes are traceable and do not silently delete obligations. | Implemented for add, merge, retire, quarantine, redact, trace checks, and package-level tests. |
| Packet operations | Fork, specialize, generalize, compose, contrast, repair, retire, quarantine, internalize, and redact operate on real packets. | Implemented at CLI and API level; operation examples need broader documentation. |
| Runtime loop | Runtime can load state, route residuals, generate packets, and save the result. | Implemented with in-memory runtime and JSON state persistence for saved ecology state. |
| Formal semantics | VET-Core syntax, static semantics, operation semantics, runtime semantics, invariants, and safety theorems compile in Lean. | Implemented in `formal/lean/VETCore` and checked by `lake build`. |
| Python formal conformance | Python operation traces map to the formal VET-Core names and required obligations. | Implemented through `verification_ecology_kit.formal_bridge`, formal schemas, golden traces, and `tests/formal`. |
| Audits | Packet ecology, residual metabolism, aperture regression, adversarial ingress, schema overclosure, and monoculture audits have documented inputs. | Implemented; examples and negative fixture coverage should grow. |
| Security | Secret and local information scanners are available and included in release checks. | Implemented with allowlist support; deeper archive scanning can improve confidence. |
| Documentation | A first-time user can understand purpose, install, run examples, and find deeper docs. | Improved README and docs navigation; API examples need more breadth. |
| Examples | Runnable examples cover common workflows and failure cases. | Implemented as a v1 baseline; new domain examples can be added without changing the release contract. |
| Tests | Unit, property, integration, golden, packaging, and security tests pass at the release threshold. | Implemented. The configured coverage gate is 92%. |
| CI and release engineering | CI gates lint, types, tests, schemas, docs, security, package contents, and wheel smoke install. | Implemented as local and workflow-facing release gates. |
| Version claim | The package must not claim stable v1 readiness while release gaps remain. | Enforced by `scripts/check_v1_readiness.py --strict`. |
| Semantic gates | Critical theory claims must be backed by executable negative checks, not only file-presence checks. | Enforced by `scripts/check_v1_readiness.py --strict` and pytest. |

## Exit Criteria

A v1 release candidate should satisfy all of the following:

- `uv sync --locked --all-extras --dev`
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy src`
- `uv run pytest --cov=verification_ecology_kit --cov-report=term-missing`
- `uv run check-jsonschema --check-metaschema src/verification_ecology_kit/schemas/*.schema.json`
- `uv run python scripts/verify_no_secrets.py .`
- `uv run python scripts/scan_local_info.py .`
- `uv run bandit -c pyproject.toml -r src scripts`
- `uv run pip-audit`
- `uvx zizmor .`
- `uv run python scripts/check_formal_coverage.py`
- `uv run python scripts/check_formal_claims.py`
- `cd formal/lean && lake build`
- `uv run mkdocs build --strict`
- `uv build --no-sources`
- `uv run python scripts/verify_package_contents.py`
- `uv run python scripts/smoke_install_wheel.py`
- `uv run python scripts/check_v1_readiness.py --strict`

## Release Rule

Do not bump the package version to a stable v1 release while the readiness
script reports gaps. If an urgent release is needed before every item is
complete, publish a release candidate and keep the residual obligations visible.

Do not claim complete VET-Core formal operational semantics unless
`lake build`, `scripts/check_formal_coverage.py`,
`scripts/check_formal_claims.py`, and the Python formal tests pass.
