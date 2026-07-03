# Pre-Publication Audit

This audit records the repository state before the first public push. It is not a release record and does not authorize a package publish, Git tag, Zenodo archive, or PyPI upload.

## Scope

- Rechecked the implementation against the Verifier Ecology Theory paper requirements and the repository prompt.
- Audited theory coverage, runtime behavior, schema surface, tests, security scanners, packaging, CI, documentation, and OS-dependent commands.
- Verified that repository metadata should use general searchable terms and the paper DOI as homepage.

## Holes Found And Closed

- Repository was not initialized and the GitHub repository did not exist. Resolution is handled after this audit by creating the repository, setting metadata, committing, and pushing.
- `tests/fixtures` and `tests/golden` were empty. Added tracked fixtures and golden cases for conformance, digest rejection, unresolved references, stale checkers, missing counter-packets, external quarantine, overclosure, schema-overclosure, authority denial, runtime history residuals, and counter-packet boundary gaps.
- Several theory records were underspecified in the public API. Added digest records, schema migration witnesses, reference edges, trace certificates, counter-packets, and boundary tester packets with serialization or witness checks.
- Runtime history residualization generated duplicate residuals across repeated runs. Added stable provenance deduplication by history event origin and scope.
- Wheel smoke testing used shell wildcard behavior that is not portable across operating systems. Replaced it with `scripts/smoke_install_wheel.py`.
- The public empty security allowlist was present but not packaged consistently. Included `security/allowlist.toml` in the source distribution.
- CI allowed documentation failures. Documentation now builds under strict mode without `|| true`.
- GitHub Actions were using mutable action tags, persisted checkout credentials, and setup-uv caching. Pinned action references to commit hashes, disabled persisted credentials, and disabled setup-uv cache.
- Dependabot updates lacked a cooldown. Added a seven-day cooldown for GitHub Actions and Python dependency updates.

## Required Local Gates

The final pre-push gate set is:

- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run mypy src`
- `uv run pytest --cov=verification_ecology_kit --cov-report=term-missing`
- `uv run python scripts/verify_no_secrets.py .`
- `uv run python scripts/scan_local_info.py .`
- `uv run check-jsonschema --check-metaschema src/verification_ecology_kit/schemas/*.schema.json`
- `uv run bandit -c pyproject.toml -r src scripts`
- `uv run pip-audit`
- `uvx zizmor .`
- `uv run mkdocs build --strict`
- `uv build --no-sources`
- `uv run python scripts/verify_package_contents.py`
- `uv run python scripts/smoke_install_wheel.py`

## Repository Metadata Target

- Description: `Python toolkit for verification auditing, residual ledgers, conformance checks, and verifier packet workflows.`
- Homepage: `https://doi.org/10.5281/zenodo.21147093`
- Topics: `python`, `verification`, `audit`, `json-schema`, `conformance`, `software-quality`, `testing`, `security`, `cli`, `governance`

## Release Status

No release, tag, package publish, or archive publish is part of this audit.
