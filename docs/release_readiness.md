# Release Readiness

This page records the release-readiness contract for `verification-ecology-kit`
`1.2.0`.

## Current Decision

`ready_for_v1.2.0: true` for local release artifacts when all commands in the
gate below pass on the current worktree.

The release decision supports the bounded formal claim for VET-Core. It does
not claim that the software proves every mathematical statement in the paper,
and it does not claim full formal verification of Python execution.

## Required Gate

Run the commands from the repository root:

```bash
uv sync --locked --all-extras --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest --cov=verification_ecology_kit --cov-report=term-missing --cov-fail-under=92
uv run check-jsonschema --check-metaschema src/verification_ecology_kit/schemas/*.schema.json
uv run python scripts/check_formal_coverage.py
uv run python scripts/check_formal_claims.py
uv run python scripts/verify_no_secrets.py .
uv run python scripts/scan_local_info.py .
uv run python scripts/check_v1_readiness.py --strict
uv run bandit -c pyproject.toml -r src scripts
uv run pip-audit
uvx zizmor .
uv run mkdocs build --strict
uv build --no-sources
uv run python scripts/verify_package_contents.py
uv run python scripts/smoke_install_wheel.py
```

Run the Lean gate from `formal/lean`:

```bash
lake build
```

## PyPI Trusted Publishing

Trusted Publishing settings:

- Project name: `verification-ecology-kit`
- Owner: `kadubon`
- Repository: `verification-ecology-kit`
- Workflow: `workflow.yml`
- Environment: `pypi`

The publish workflow must run only from version tags, use `id-token: write`,
avoid a PyPI token secret, and keep repository permissions read-only except
where a job explicitly needs a narrower elevated permission.

## No-Release Conditions

Do not publish a stable release if any of the following are true:

- `scripts/check_v1_readiness.py --strict` reports a gap.
- `scripts/check_formal_coverage.py` or `scripts/check_formal_claims.py`
  reports a gap.
- `lake build` fails under the pinned Lean toolchain.
- Any required schema listed in that script is missing.
- `tests/golden/theory_coverage.expected.json` contains `partial` or
  `not_implemented`.
- README, pyproject metadata, or CHANGELOG contradict the current v1 claim.
- The package artifact contains local paths, private files, notebooks,
  generated PDFs, TeX build artifacts, `.env` files, private keys, or hidden
  scratch files.
- The wheel smoke install does not print the same version as `pyproject.toml`.

## Artifact Evidence

The local release artifact evidence is:

- `dist/verification_ecology_kit-1.2.0.tar.gz`
- `dist/verification_ecology_kit-1.2.0-py3-none-any.whl`
- package contents audit decision: `pass`
- smoke install version: `1.2.0`
