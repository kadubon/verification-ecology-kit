# Capacity release evidence

Initial inspected default HEAD: `718a481db6752cb5a86417e46fb5234a7257cfec`.
The worktree was clean. GitHub and public PyPI both published 1.2.0; 1.3.0 was unused.
Open PRs were unrelated dependency updates. No companion repository was modified.
GitHub reported no main-branch protection/rulesets or protected-environment review
rules. No policy bypass is authorized or used. Account-side Trusted Publisher identity
must still be verified by actual publication; workflow YAML alone is insufficient.

Wiki: not applicable. GitHub's repository API reports `has_wiki: false` and the Wiki
git remote is unavailable. No Wiki hosting was enabled. Canonical docs remain here.

Baseline Windows/Python 3.13: 155 tests passed, 92.75% combined statement/branch
coverage. The initial bare `lake build` had no default targets and did not establish
proof compilation. Explicit target compilation exposed existing errors, subsequently
fixed without changing theorem statements or predicates. The full VET-Core import
closure and new CapacityCore now build under the pinned Lean 4.12.0 toolchain.

Local validation: 219 tests passed on Windows/Python 3.13; statement coverage
95.86%, branch coverage 85.82%, combined coverage 93.64% (92% combined gate).
All six selected faults were killed. Strict typing/lint, metaschema checks, generated
docs/fixtures drift, strict MkDocs, source/archive scans, Bandit, dependency audit,
Zizmor, formal coverage/claims and pinned Lean compilation passed. The built wheel
installed in a fresh external environment and completed offline doctor/conformance,
14 capacity scenarios and pinned interchange checks. CI and public publication are
separate pending gates. The vulnerable development-tool pip lock was updated to 26.2.1.

Publication is pending. IMPLEMENTED, LOCALLY_VERIFIED, FORMAL_GATES_PASSED,
CI_PASSED, PUSHED, MERGED, DOCS_UPDATED, GITHUB_RELEASED, PYPI_PUBLISHED and
PUBLIC_INDEX_VERIFIED must be reported separately after their actual checks. No tag
or release should be interpreted as proof of a successful PyPI install.

## Exact publication checks

The tag workflow builds once, tests the wheel, checks both archives, generates
`SHA256SUMS`, and uploads the build output. Windows/macOS install those same bytes.
The publish job downloads that artifact and verifies the manifest, then uses the
existing `workflow.yml` / `pypi` OIDC identity. It never rebuilds or uses skip-existing.

After publication, install the exact version from `https://pypi.org/simple` with
isolated pip, disabled cache and an installation report in a fresh environment outside
the checkout. Verify metadata/import origin, `pip check`, doctor/core conformance,
the capacity installed check with socket connections blocked, and wheel/sdist hashes
against PyPI JSON, GitHub assets and the manifest. Record the precise tag commit and
workflow run/attempt. Ordinary installation does not execute Lean proofs.
