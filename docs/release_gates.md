# Release Gates

This project uses release gates to separate useful development snapshots from a
stable public claim.

## Gate Levels

| Gate | Meaning | Required before |
| --- | --- | --- |
| Development | The package installs locally and the changed feature has targeted tests. | Merging ordinary changes. |
| Public snapshot | Core lint, type, test, docs, schema, package, and security checks pass. | Publishing a non-stable package or tag. |
| V1 candidate | All readiness gaps are either closed or documented as release-blocking residuals. | Creating a v1 release candidate. |
| V1 stable | The readiness script passes in strict mode and the package no longer carries alpha status. | Publishing a v1 stable release. |
| Formal VET-Core | Lean, formal coverage, formal claim control, and Python formal conformance tests pass. | Publishing a release that claims complete VET-Core formal operational semantics. |

## Standard Local Gate

Run this before shipping an ordinary change:

```bash
uv sync --locked --all-extras --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
```

## Formal Gate

Run this before any release that carries the v1.2.0 formal VET-Core claim:

```bash
uv run pytest tests/formal --no-cov
uv run python scripts/check_formal_coverage.py
uv run python scripts/check_formal_claims.py
cd formal/lean
lake build
```

The formal gate is release-blocking for the claim:

> verification-ecology-kit provides a complete formal operational semantics for
> the VET-Core implemented by this package, with machine-checked safety
> theorems and Python conformance tests against the formal semantics.

## Publication Gate

Run this before publishing a package artifact:

```bash
uv run python scripts/verify_no_secrets.py .
uv run python scripts/scan_local_info.py .
uv run check-jsonschema --check-metaschema src/verification_ecology_kit/schemas/*.schema.json
uv run bandit -c pyproject.toml -r src scripts
uv run pip-audit
uvx zizmor .
uv run mkdocs build --strict
uv build --no-sources
uv run python scripts/verify_package_contents.py
uv run python scripts/smoke_install_wheel.py
```

## V1 Gate

Run this before a v1 release:

```bash
uv run python scripts/check_v1_readiness.py --strict
```

The script checks repository structure, documentation links, schema coverage,
CLI behavior expectations, formal coverage, formal claim control, and
version-claim safety. It is not a replacement for the full test, Lean, and
security gate; it is the release-readiness summary.

## Failure Handling

When a gate fails, do one of the following:

- fix the issue and rerun the same gate
- document the issue as a residual obligation and keep the stable version claim below the affected release
- publish only a release candidate if the remaining gap is known and visible

Do not hide a failed gate by changing the command, lowering a threshold, or
removing the affected check without adding a replacement.
