# Capacity requirement and evidence matrix

This matrix maps the additive V1–V4 work to executable artifacts. Publication status
is recorded separately in [release evidence](capacity_release.md). A local passing
check is not a claim that CI, PyPI publication or public-index installation passed.

| Milestone / obligation | Implementation | Test / formal boundary |
| --- | --- | --- |
| V1 closed finite contracts and exact units | `capacity/model.py`, four capacity schemas | malformed/closed-record tests; bounded rational/integer coordinates |
| V1 domain, validity and exposure constraints | service/work/action registration, `checker.py` | expiry, separation, correlated-wrapper and shared-pool controls |
| V1 event replay and attempt accounting | `reducer.py`, `runtime.py` | all five outcomes, stale revisions, conflicting retries, unknown dispatch, interrupted writes |
| V1 observed versus forecast boundary | `report.py`, `reducer.py` | observed fields stay null; relabeled observed result rejected |
| V2 finite allocation and protected work | `selector.py`, `baselines.py` | protected/flood/burst/outage; separate tiny exhaustive oracle in property tests |
| V2 independent schedule check | `checker.py` | witness tampering, cost bounds, separation, predecessors; no selector import |
| V2 joint branches and investment | `examples.py`, success/negative prerequisites | investment feasible, overpriced baseline wins, unsupported candidate has no capacity credit |
| V2 integrated residual path | `RuntimeEngine.capacity`, `CapacityRuntime` | existing store, residual binding, conformance envelope, repair residual, deduplicated follow-ups |
| V3 accounting proofs | `CapacityCore/Accounting.lean` | concrete guarded transitions; theorem list in formal guide |
| V3 actual Python trace correspondence | `capacity/formal.py` | actual reducer traces, independent conservation evaluator, negative controls |
| V3 CCR proposals | `interchange.py`, pinned schema fixture | schema-valid proposals only; CCR reservation/reward/approval unsupported locally |
| V3 CAIT-readable output | partial VEK-owned envelope | no arrival verdict, no CAIT certificate-conformance claim |
| V4 installed commands/scenarios | `capacity/cli.py`, `installed_check.py` | real JSON store CLI tests; offline installed-wheel scenarios |
| V4 software/formal gates | existing workflow plus explicit Lean defaults and fault checks | unchanged Python 3.11–3.13, strict typing/lint, 92% combined coverage, security/docs/package checks |
| V4 artifact identity | build artifact, manifest, download-only publisher | installation on Linux/Windows/macOS before tag publish job |
| V4 public delivery | normal PR/check policy, tag-triggered OIDC publishing | release evidence remains incomplete until exact public-PyPI hashes and installation verified |

The resource layer enforces registered service assumptions, not their truth in the
world. No external empirical collective-intelligence acceleration experiment was
performed. Synthetic scenarios are software/formal controls, not measured acceleration.
