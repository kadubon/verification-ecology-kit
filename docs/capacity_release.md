# Capacity release evidence

Initial inspected default HEAD: `718a481db6752cb5a86417e46fb5234a7257cfec`.
The worktree was clean. GitHub and public PyPI both published 1.2.0; 1.3.0 was unused.
Open PRs were unrelated dependency updates. No companion repository was modified.
GitHub reported no main-branch protection/rulesets or protected-environment review
rules. No policy bypass was used. Account-side Trusted Publisher identity was
verified by the successful tag publication; workflow YAML alone is insufficient.

Wiki: not applicable. GitHub's repository API reports `has_wiki: false` and the Wiki
git remote is unavailable. No Wiki hosting was enabled. Canonical docs remain here.

Baseline Windows/Python 3.13: 155 tests passed, 92.75% combined statement/branch
coverage. The initial bare `lake build` had no default targets and did not establish
proof compilation. Explicit target compilation exposed existing errors, subsequently
fixed without changing theorem statements or predicates. The full VET-Core import
closure and new CapacityCore now build under the pinned Lean 4.12.0 toolchain.

Local validation: 221 tests passed on Windows with each of Python 3.11, 3.12 and
3.13; Python 3.13 statement coverage 95.89%, branch coverage 85.87%, combined
coverage 93.68% (92% combined gate).
All six selected faults were killed. Strict typing/lint, metaschema checks, generated
docs/fixtures drift, strict MkDocs, source/archive scans, Bandit, dependency audit,
Zizmor, formal coverage/claims and pinned Lean compilation passed. The built wheel
installed in a fresh external environment and completed offline doctor/conformance,
14 capacity scenarios and pinned interchange checks. The vulnerable development-tool
pip lock was updated to 26.2.1.

## Published 1.3.0 evidence

[PR #7](https://github.com/kadubon/verification-ecology-kit/pull/7) merged normally as
`b07998135cb9dccde1e67db3c6ed77fdec847e09`. Its tree matches tested PR head
`113a24612f5c5b439b2d3119757e2a9fad13ccfa` exactly. The temporary CI queue barrier
resolved before merging. No administrator check override or companion waiver was used.

The [PR run](https://github.com/kadubon/verification-ecology-kit/actions/runs/34700811743),
[merged-main run](https://github.com/kadubon/verification-ecology-kit/actions/runs/34725158272)
and [v1.3.0 tag run, attempt 1](https://github.com/kadubon/verification-ecology-kit/actions/runs/34725243732)
passed all quality gates, including Linux/Python 3.11–3.13, Lean, fault checks, build,
and installation of the same wheel on Windows/macOS. The tag run's `publish` job
also succeeded using the existing `workflow.yml` / `pypi` Trusted Publisher identity;
no environment approval was pending.

[GitHub Release](https://github.com/kadubon/verification-ecology-kit/releases/tag/v1.3.0)
and [public PyPI 1.3.0](https://pypi.org/project/verification-ecology-kit/1.3.0/)
contain the identical tag-workflow distributions:

```text
4182b48369823b06ea35b9c234ddcea824bf53fe6ece5f068200edf11ddd23ca  verification_ecology_kit-1.3.0-py3-none-any.whl
f0e1613df6619b0a127c313e938705c848fde0d0cdb4e351cb5e1c74ae68bae2  verification_ecology_kit-1.3.0.tar.gz
```

Fresh external Windows environments on Python 3.13 and 3.14 installed exact
`verification-ecology-kit==1.3.0` using isolated pip, `--no-cache-dir`, public
`https://pypi.org/simple`, and installation reports. Package and dependency URLs were
verified as public `files.pythonhosted.org` downloads. Metadata/version and import
origin inside the fresh environment, `pip check`, doctor/core conformance, all 14
capacity scenarios and the integrated interchange checks passed. Socket connections
were blocked during example execution. Python 3.14 here is an additional installed
smoke result, not an expansion of the full Python 3.11–3.13 test matrix.

Publicly downloaded wheel/sdist hashes match the workflow artifacts, release assets
and both manifests; the pip report matches the wheel hash. PyPI's simple JSON index
advertised no provenance for either file: no attestation verification is claimed.
The separate source/CI Lean evidence does not come from package installation.

| Status | Result |
| --- | --- |
| IMPLEMENTED | V1 capacity/workload semantics, V2 bounded allocation, V3 formal/conformance, V4 publication |
| LOCALLY_VERIFIED | Passed; 221 tests per supported Python version |
| FORMAL_GATES_PASSED | Passed; all 15 original statements preserved, 11 new accounting theorems |
| CI_PASSED | PR, merged-main and tag runs passed |
| PUSHED | Feature and immutable v1.3.0 tag pushed |
| MERGED | PR #7 at the commit above |
| DOCS_UPDATED | Canonical guides and this post-publication record |
| WIKI_UPDATED_OR_NOT_APPLICABLE | Not applicable; existing Wiki disabled |
| GITHUB_RELEASED | v1.3.0, with wheel, sdist and SHA256SUMS |
| PYPI_PUBLISHED | 1.3.0 via actual successful Trusted Publishing |
| PUBLIC_INDEX_VERIFIED | Passed exact public-index installation and byte identity checks |
| BLOCKED | None remaining for this bounded release scope |

No external empirical collective-intelligence acceleration experiment was performed.
VEK schedules and accounts for bounded verification work under declared evidence/model
assumptions. Lean proves the stated formal subsystem properties; Python is
conformance-tested, not wholly formally verified. A checked schedule, a verifier packet
or a completed check does not establish independent errors, scientific truth, AGI/ASI
or execution authority. The experimental profile's limits in the capacity guide remain.

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
