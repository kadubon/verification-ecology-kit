"""Check whether the repository is allowed to claim v1 readiness."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

REQUIRED_DOCS = (
    "README.md",
    "docs/quickstart.md",
    "docs/concepts.md",
    "docs/theory_mapping.md",
    "docs/data_model.md",
    "docs/schemas.md",
    "docs/conformance.md",
    "docs/audits.md",
    "docs/cli.md",
    "docs/examples.md",
    "docs/security.md",
    "docs/v1_audit.md",
    "docs/v1_readiness.md",
    "docs/release_readiness.md",
    "docs/release_gates.md",
)

REQUIRED_SCHEMAS = (
    "aperture.schema.json",
    "audit-report.schema.json",
    "auth-inputs.schema.json",
    "authority-decision.schema.json",
    "boundary-record.schema.json",
    "carrier-registry.schema.json",
    "certification-profile.schema.json",
    "certification-record.schema.json",
    "checker-registry.schema.json",
    "conformance-report.schema.json",
    "continuation-specification.schema.json",
    "contract-registry.schema.json",
    "counterexample-channel.schema.json",
    "digest-record.schema.json",
    "frontier-profile.schema.json",
    "judgment-record.schema.json",
    "ledger-event.schema.json",
    "lifecycle-status-event.schema.json",
    "maturity-profile.schema.json",
    "overclosure-witness.schema.json",
    "reachability-certificate.schema.json",
    "reference-edge.schema.json",
    "residual-ledger.schema.json",
    "residual-record.schema.json",
    "runtime-report.schema.json",
    "schema-catalogue.schema.json",
    "schema-migration-witness.schema.json",
    "sound-gap-residual.schema.json",
    "status-view.schema.json",
    "vet-bundle.schema.json",
    "vet-object-envelope.schema.json",
    "vet-object-ref.schema.json",
    "verifier-packet.schema.json",
)

REQUIRED_GOLDEN = ("tests/golden/theory_coverage.expected.json",)

REQUIRED_EXAMPLES = (
    "examples/basic_packet.py",
    "examples/residual_ledger.py",
    "examples/operational_bundle.py",
    "examples/external_packet_quarantine.py",
    "examples/overclosure_audit.py",
    "examples/runtime_loop.py",
    "examples/federated_bundle.py",
    "examples/authority_gate.py",
    "examples/reachability_certificate.py",
    "examples/schema_migration.py",
)

THEORY_TERMS = (
    "verifier packet",
    "residual",
    "residual ledger",
    "conformance",
    "authority",
    "aperture",
    "monoculture",
    "schema overclosure",
)


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any readiness gap remains, even before a stable v1 version.",
    )
    args = parser.parse_args(argv)

    pyproject = _read_pyproject()
    version = str(pyproject["project"]["version"])
    classifiers = [str(item) for item in pyproject["project"].get("classifiers", [])]
    pytest_addopts = str(
        pyproject.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("addopts", "")
    )
    gates = _collect_gates(
        version=version,
        classifiers=classifiers,
        pytest_addopts=pytest_addopts,
    )
    gaps = [gate for gate in gates if not gate.passed]
    claims_v1 = _claims_v1(version)
    fail_release = bool(gaps) and (claims_v1 or args.strict)

    report = {
        "version": version,
        "claims_v1_or_later": claims_v1,
        "ready_for_v1_0_0": not gaps,
        "ready_for_v1_1_0": not gaps,
        "strict": args.strict,
        "decision": "pass" if not fail_release else "fail",
        "gates": [gate.to_dict() for gate in gates],
        "gaps": [gate.to_dict() for gate in gaps],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if fail_release else 0


def _read_pyproject() -> dict[str, Any]:
    pyproject = ROOT / "pyproject.toml"
    with pyproject.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError("pyproject.toml did not parse as a table")
    return data


def _collect_gates(
    *,
    version: str,
    classifiers: list[str],
    pytest_addopts: str,
) -> list[Gate]:
    cli = _read_text("src/verification_ecology_kit/cli.py")
    readme = _read_text("README.md")
    mkdocs = _read_text("mkdocs.yml")
    theory_mapping = _read_text("docs/theory_mapping.md")
    v1_audit = _read_text("docs/v1_audit.md")
    readiness = _read_text("docs/v1_readiness.md")
    release_gates = _read_text("docs/release_gates.md")
    changelog = _read_text("CHANGELOG.md")

    return [
        _gate_required_docs(),
        _gate_mkdocs_nav(mkdocs),
        _gate_required_schemas(),
        _gate_required_golden(),
        _gate_required_examples(),
        _gate_readme_links(readme),
        _gate_theory_terms(theory_mapping),
        _gate_theory_coverage_fixture(),
        _gate_cli_real_packet_inputs(cli),
        _gate_cli_real_audit_inputs(cli),
        _gate_readiness_records_release_rule(readiness),
        _gate_release_gates_include_strict_check(release_gates),
        _gate_workflows_use_locked_sync(),
        _gate_semantic_regression_checks(),
        _gate_v1_audit_semantic_statuses(v1_audit),
        _gate_schema_semantic_coverage(),
        _gate_no_placeholder_terms(),
        _gate_changelog_v1(changelog),
        _gate_changelog_current_version(changelog, version),
        _gate_v1_version_target(version, classifiers),
        _gate_coverage_threshold(pytest_addopts),
        _gate_version_claim_is_safe(version, classifiers, readme),
    ]


def _gate_required_docs() -> Gate:
    missing = [path for path in REQUIRED_DOCS if not (ROOT / path).is_file()]
    return Gate(
        "required_docs",
        not missing,
        "all required docs are present" if not missing else f"missing: {', '.join(missing)}",
    )


def _gate_mkdocs_nav(mkdocs: str) -> Gate:
    required = (
        "v1_audit.md",
        "v1_readiness.md",
        "release_readiness.md",
        "release_gates.md",
        "cli.md",
        "audits.md",
    )
    missing = [item for item in required if item not in mkdocs]
    return Gate(
        "mkdocs_navigation",
        not missing,
        "nav includes release and CLI docs" if not missing else f"missing nav: {missing}",
    )


def _gate_required_schemas() -> Gate:
    schema_root = ROOT / "src" / "verification_ecology_kit" / "schemas"
    missing = [name for name in REQUIRED_SCHEMAS if not (schema_root / name).is_file()]
    return Gate(
        "required_schemas",
        not missing,
        "required schemas are present" if not missing else f"missing schemas: {missing}",
    )


def _gate_required_golden() -> Gate:
    missing = [path for path in REQUIRED_GOLDEN if not (ROOT / path).is_file()]
    return Gate(
        "required_golden",
        not missing,
        "required golden fixtures are present" if not missing else f"missing: {missing}",
    )


def _gate_required_examples() -> Gate:
    missing = [path for path in REQUIRED_EXAMPLES if not (ROOT / path).is_file()]
    return Gate(
        "required_examples",
        not missing,
        "required examples are present" if not missing else f"missing: {missing}",
    )


def _gate_readme_links(readme: str) -> Gate:
    required = (
        "docs/cli.md",
        "docs/v1_audit.md",
        "docs/v1_readiness.md",
        "docs/release_readiness.md",
        "docs/release_gates.md",
    )
    missing = [item for item in required if item not in readme]
    return Gate(
        "readme_navigation",
        not missing,
        "README links key docs" if not missing else f"missing README links: {missing}",
    )


def _gate_theory_terms(theory_mapping: str) -> Gate:
    normalized = theory_mapping.lower()
    missing = [term for term in THEORY_TERMS if term not in normalized]
    return Gate(
        "theory_mapping_terms",
        not missing,
        "theory mapping covers core terms" if not missing else f"missing terms: {missing}",
    )


def _gate_theory_coverage_fixture() -> Gate:
    path = ROOT / "tests" / "golden" / "theory_coverage.expected.json"
    if not path.is_file():
        return Gate("theory_coverage_fixture", False, "theory coverage fixture is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    terms = data.get("terms", [])
    if not isinstance(terms, list):
        return Gate("theory_coverage_fixture", False, "terms must be a list")
    bad_statuses = [
        str(item.get("theory_term", "<unknown>"))
        for item in terms
        if isinstance(item, dict) and item.get("status") not in {"implemented", "not_applicable"}
    ]
    missing_schema = [
        str(item.get("theory_term", "<unknown>"))
        for item in terms
        if isinstance(item, dict) and not str(item.get("schema", "")).strip()
    ]
    missing_docs = [
        str(item.get("theory_term", "<unknown>"))
        for item in terms
        if isinstance(item, dict) and not (ROOT / str(item.get("docs", ""))).is_file()
    ]
    too_short = len(terms) < 50
    passed = not bad_statuses and not missing_schema and not missing_docs and not too_short
    detail = "theory coverage fixture is complete"
    if not passed:
        detail = (
            f"bad_statuses={bad_statuses}; missing_schema={missing_schema}; "
            f"missing_docs={missing_docs}; term_count={len(terms)}"
        )
    return Gate("theory_coverage_fixture", passed, detail)


def _gate_cli_real_packet_inputs(cli: str) -> Gate:
    operate_body = _function_body(cli, "_packet_operate")
    checks = {
        "packet input argument": 'operate.add_argument("inputs"' in cli,
        "output path argument": 'operate.add_argument("--out"' in cli,
        "loader use": "_packet_from_json(_load_json" in operate_body,
        "no minimal fixture": "VerifierPacket.minimal()" not in operate_body,
        "writes output": "_write_json(" in operate_body,
    }
    missing = [name for name, passed in checks.items() if not passed]
    return Gate(
        "cli_packet_real_inputs",
        not missing,
        "packet operations consume input files" if not missing else f"missing: {missing}",
    )


def _gate_cli_real_audit_inputs(cli: str) -> Gate:
    audit_body = _function_body(cli, "_audit")
    checks = {
        "audit input argument": 'cmd.add_argument("input")' in cli,
        "required input": 'cmd.add_argument("input", nargs="?")' not in cli,
        "loader use": "data = _load_json(Path(args.input))" in audit_body,
        "no minimal fixture": "VerifierPacket.minimal()" not in audit_body,
        "packet population loader": "_packets_from_audit_input(data)" in audit_body,
    }
    missing = [name for name, passed in checks.items() if not passed]
    return Gate(
        "cli_audit_real_inputs",
        not missing,
        "audits consume input files" if not missing else f"missing: {missing}",
    )


def _gate_readiness_records_release_rule(readiness: str) -> Gate:
    required = ("Do not bump", "stable v1", "scripts/check_v1_readiness.py --strict")
    missing = [item for item in required if item not in readiness]
    return Gate(
        "readiness_release_rule",
        not missing,
        "readiness doc states release rule" if not missing else f"missing text: {missing}",
    )


def _gate_release_gates_include_strict_check(release_gates: str) -> Gate:
    passed = "scripts/check_v1_readiness.py --strict" in release_gates
    return Gate(
        "release_gate_strict_check",
        passed,
        "release gates include strict readiness check"
        if passed
        else "strict readiness command missing",
    )


def _gate_workflows_use_locked_sync() -> Gate:
    workflow = _read_text(".github/workflows/workflow.yml")
    unlocked = "uv sync --all-extras --dev" in workflow
    locked = "uv sync --locked --all-extras --dev" in workflow
    return Gate(
        "workflow_locked_uv_sync",
        locked and not unlocked,
        "workflows use locked dependency sync"
        if locked and not unlocked
        else "workflow still contains unlocked uv sync",
    )


def _gate_semantic_regression_checks() -> Gate:
    failures: list[str] = []
    try:
        from verification_ecology_kit.audit.security import scan_secrets
        from verification_ecology_kit.digest import Digest
        from verification_ecology_kit.errors import VEKError
        from verification_ecology_kit.model.aperture import Aperture, CapacityRecord
        from verification_ecology_kit.model.authority import AuthorityDecision, AuthorityEngine
        from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
        from verification_ecology_kit.model.frontier import (
            FrontierComparison,
            FrontierEntry,
            VerifiableFrontierProfile,
        )
        from verification_ecology_kit.model.packets import VerifierPacket
        from verification_ecology_kit.model.records import (
            AuthorityAction,
            AuthorityDecisionValue,
            ConformanceProfile,
            LifecycleStatus,
            ResidualKind,
        )
        from verification_ecology_kit.model.residuals import ResidualRecord
        from verification_ecology_kit.operations.base import PacketOperationEngine
        from verification_ecology_kit.references import (
            ObjectEnvelope,
            SchemaCatalogue,
            resolve_pointer,
        )
        from verification_ecology_kit.result import CheckOutcome
        from verification_ecology_kit.runtime.engine import RuntimeEngine
        from verification_ecology_kit.runtime.in_memory import InMemoryStore
    except Exception as exc:  # pragma: no cover - exercised by readiness command
        return Gate("semantic_regressions", False, f"imports failed: {exc}")

    empty = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [],
    )
    if ConformanceEngine().run(empty).decision.value != "reject":
        failures.append("operational empty bundle was not rejected")

    for pointer in ("/items/-1", "/items/01"):
        try:
            resolve_pointer({"items": ["x"]}, pointer)
            failures.append(f"pointer accepted: {pointer}")
        except VEKError:
            pass

    auth = AuthorityDecision(
        authority_decision_id="a",
        object_id="obj",
        schema_version="1",
        canonical_digest=Digest("sha256", "abc"),
        lifecycle_status=LifecycleStatus.ACTIVE,
        policy_id="p",
        action=AuthorityAction.DEPLOYMENT,
        decision=AuthorityDecisionValue.ALLOW,
        required_support_refs=("support",),
        support_statuses={"support": LifecycleStatus.STALE},
    )
    decision, authority_result = AuthorityEngine().aggregate(
        AuthorityAction.DEPLOYMENT,
        [auth],
        required_support_refs=("support",),
    )
    if decision != AuthorityDecisionValue.DENY or authority_result.passed:
        failures.append("stale authority support was allowed")

    subject = ObjectEnvelope("subject", "schema", "1.0", {"status": "active"})
    subject.refresh_digest()
    subject_ref = subject.ref(bundle_id="b")
    bad_record = {
        "judgment_id": "j",
        "judgment_kind": "support",
        "subject": subject_ref.to_dict(),
        "checker_or_policy_ref": "checker",
        "contract_version": "bad-contract",
        "schema_version": "1",
        "object_id": "subject",
        "canonical_digest": subject.canonical_digest.to_dict(),
        "use_context_ref": "u",
        "use_context": {
            "subject_ref": subject_ref.to_dict(),
            "resolved_input_ref": subject_ref.to_dict(),
            "canonical_input_ref": subject_ref.to_dict(),
            "input_digest": subject.canonical_digest.to_dict(),
        },
        "contract": {
            "judgment_kind": "support",
            "subject_type": "schema",
            "allowed_results": ["pass"],
            "version": "actual-contract",
        },
        "canonical_input_ref": subject_ref.to_dict(),
        "input_digest": subject.canonical_digest.to_dict(),
        "result": "pass",
        "jvalid_result": "pass",
        "status": "active",
    }
    bad_jvalid_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [subject],
        judgment_records=[bad_record],
    )
    if ConformanceEngine().run(bad_jvalid_bundle).decision.value != "reject":
        failures.append("declared JValid pass bypassed reconstruction")

    stale_support = ObjectEnvelope("support", "schema", "1.0", {"status": "stale"})
    stale_support.refresh_digest()
    stale_bundle = VetBundle(
        "b",
        "1",
        ConformanceProfile.OPERATIONAL,
        SchemaCatalogue("cat", {"schema": ("1.0",)}),
        [subject, stale_support],
        authority_decisions=[
            {
                "authority_decision_id": "declared-allow",
                "decision": "allow",
                "lifecycle_status": "active",
                "auth_inputs": {
                    "auth_inputs_ref": "ai",
                    "object_id": "subject",
                    "schema_version": "1",
                    "canonical_digest": subject.canonical_digest.to_dict(),
                    "candidate_ref": "subject",
                    "action": "local_use",
                    "support_refs": ["support"],
                },
            }
        ],
    )
    if ConformanceEngine().run(stale_bundle).decision.value != "reject":
        failures.append("conformance authority allowed stale support evidence")

    engine = PacketOperationEngine()
    left = VerifierPacket.minimal()
    right = VerifierPacket.minimal()
    right.residual_obligations.append(
        ResidualRecord(ResidualKind.UNRESOLVED, right.packet_id, ("right",), "preserve")
    )
    operation = engine.compose(left, right)
    if operation.admissibility.result == CheckOutcome.PASS:
        failures.append("composition admissibility passed without boundary/counter checks")
    parent = VerifierPacket.minimal()
    parent.counter_packet_refs.append("counter-parent")
    child = VerifierPacket.minimal()
    child.packet_id = "child"
    invariant_result = engine._check_ecological_invariants((parent,), child, boundary_checked=True)
    if invariant_result.passed:
        failures.append("packet operation accepted dropped ecological invariant")
    external = VerifierPacket.from_external_candidate()
    internalized = engine.internalize(external, translated=False, boundary_checked=False)
    if internalized.admissibility.result == CheckOutcome.PASS:
        failures.append("external packet internalized without translation/counter/residual")

    store = InMemoryStore()
    state = store.load()
    state.residual_ledger.add(
        ResidualRecord(ResidualKind.UNRESOLVED, "history", ("unknown",), "generate")
    )
    runtime_report = RuntimeEngine(store=store).run_once().to_dict()
    for key in ("frontier_updates", "aperture_updates", "schema_checks", "lineage_checks"):
        if not runtime_report.get(key):
            failures.append(f"runtime report lacks {key}")
        if any(not isinstance(item, dict) for item in runtime_report.get(key, [])):
            failures.append(f"runtime report {key} contains non-structured labels")
    if any(not isinstance(item, dict) for item in runtime_report.get("reachability_checks", [])):
        failures.append("runtime reachability check is not structured")

    ledger = state.residual_ledger
    if ledger.events:
        ledger.events[0] = ledger.events[0].__class__(
            **{**ledger.events[0].to_dict(), "post_state_digest": "tampered"}
        )
        if ledger.trace_ok().passed:
            failures.append("ledger trace accepted tampered event digest")

    before_frontier = VerifiableFrontierProfile(
        [FrontierEntry("u", "transform", ("p1",), ("r1",), ("1h",))]
    )
    after_frontier = VerifiableFrontierProfile(
        [FrontierEntry("u", "transform", ("p1", "p2"), ("r1",), ("1h",))]
    )
    if (
        before_frontier.compare(after_frontier, before_packet_count=1, after_packet_count=2)
        != FrontierComparison.PACKET_SPAM
    ):
        failures.append("frontier packet multiplication was not detected as packet spam")
    before_aperture = Aperture(
        question_form_capacity=CapacityRecord("question", feasible_capacity=2)
    )
    after_aperture = Aperture(
        question_form_capacity=CapacityRecord("question", feasible_capacity=1)
    )
    if before_aperture.compare(after_aperture).value != "narrowed_without_residual":
        failures.append("silent aperture narrowing was not detected")

    json_store_source = _read_text("src/verification_ecology_kit/runtime/json_store.py")
    if "verification_ecology_kit.cli" in json_store_source:
        failures.append("JsonStore imports private CLI loaders")
    if "NamedTemporaryFile" not in json_store_source or "os.replace" not in json_store_source:
        failures.append("JsonStore save is not visibly atomic")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        token = "github_pat_" + "A" * 30
        (root / "secret.txt").write_text(token, encoding="utf-8")
        raw_report = scan_secrets(root)
        if raw_report.decision != "quarantine" or token in raw_report.to_json():
            failures.append("secret scanner failed detection or redaction")
        allowlist = root / "allowlist.toml"
        allowlist.write_text(
            '[secrets]\nvalues = ["' + token + '"]\nregexes = []\npaths = []\n',
            encoding="utf-8",
        )
        if scan_secrets(root, allowlist_path=allowlist).decision != "pass":
            failures.append("secret scanner did not honor TOML allowlist")

    return Gate(
        "semantic_regressions",
        not failures,
        "semantic negative checks pass" if not failures else "; ".join(failures),
    )


def _gate_v1_audit_semantic_statuses(v1_audit: str) -> Gate:
    semantic_rows = (
        "JValid",
        "Authority aggregation",
        "ResidualLedger",
        "TraceOK",
        "RuntimeEngine",
        "LocalInternalization pipeline",
    )
    bad: list[str] = []
    for row_name in semantic_rows:
        pattern = re.compile(rf"^\| {re.escape(row_name)} \|.*\| implemented \|$", re.M)
        if pattern.search(v1_audit):
            bad.append(row_name)
    allowed_statuses = (
        "implemented",
        "schema-backed",
        "operational-check",
        "partial-semantic",
        "documented-interface",
        "residualized",
    )
    missing_status_note = "Status values:" not in v1_audit or not all(
        status in v1_audit for status in allowed_statuses
    )
    passed = not bad and not missing_status_note
    detail = "semantic audit rows use precise status vocabulary"
    if not passed:
        detail = f"overstated={bad}; missing_status_note={missing_status_note}"
    return Gate("v1_audit_semantic_statuses", passed, detail)


def _gate_schema_semantic_coverage() -> Gate:
    packet_schema = _read_text("src/verification_ecology_kit/schemas/verifier-packet.schema.json")
    bundle_schema = _read_text("src/verification_ecology_kit/schemas/vet-bundle.schema.json")
    runtime_schema = _read_text("src/verification_ecology_kit/schemas/runtime-report.schema.json")
    required = {
        "anti_overclosure": packet_schema,
        "residual_liveness": packet_schema,
        "inherited_residuals": packet_schema,
        "translation_residual_refs": packet_schema,
        "schema-catalogue.schema.json": bundle_schema,
        "authority-decision.schema.json": bundle_schema,
        "judgment-record.schema.json": bundle_schema,
        "frontier_updates": runtime_schema,
        "aperture_updates": runtime_schema,
        "lineage_checks": runtime_schema,
    }
    missing = [term for term, source in required.items() if term not in source]
    return Gate(
        "schema_semantic_coverage",
        not missing,
        "schemas expose v1.1 semantic fields" if not missing else f"missing: {missing}",
    )


def _gate_no_placeholder_terms() -> Gate:
    patterns = ("TODO", "FIXME", "placeholder", "toy", "demo-only", "NotImplementedError")
    scanned_roots = ("src", "docs", "scripts", "tests", "README.md")
    findings: list[str] = []
    for root_name in scanned_roots:
        root = ROOT / root_name
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if path.name == "check_v1_readiness.py":
                continue
            if not path.is_file() or path.suffix in {".pyc", ".png", ".jpg", ".gif"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in patterns:
                if pattern in text:
                    findings.append(f"{path.relative_to(ROOT)}:{pattern}")
    return Gate(
        "no_placeholder_terms",
        not findings,
        "no placeholder terms found" if not findings else "; ".join(findings[:10]),
    )


def _gate_changelog_v1(changelog: str) -> Gate:
    passed = "## 1.0.0" in changelog
    return Gate(
        "changelog_v1",
        passed,
        "CHANGELOG has v1.0.0 entry" if passed else "CHANGELOG lacks v1.0.0 entry",
    )


def _gate_changelog_current_version(changelog: str, version: str) -> Gate:
    heading = f"## {version}"
    passed = heading in changelog
    return Gate(
        "changelog_current_version",
        passed,
        f"CHANGELOG has {version} entry" if passed else f"CHANGELOG lacks {version} entry",
    )


def _gate_v1_version_target(version: str, classifiers: list[str]) -> Gate:
    alpha = any("Alpha" in item for item in classifiers)
    passed = _claims_v1(version) and not alpha
    if passed:
        detail = "package metadata claims a non-alpha v1 release"
    elif not _claims_v1(version):
        detail = f"package version is still {version}, not a v1 candidate"
    else:
        detail = "package metadata still contains an alpha classifier"
    return Gate("v1_version_target", passed, detail)


def _gate_coverage_threshold(pytest_addopts: str) -> Gate:
    match = re.search(r"--cov-fail-under=(\d+)", pytest_addopts)
    threshold = int(match.group(1)) if match else 0
    passed = threshold >= 92
    detail = (
        f"coverage fail-under is {threshold}"
        if passed
        else f"coverage fail-under is {threshold}; v1 target is 92"
    )
    return Gate("coverage_threshold", passed, detail)


def _gate_version_claim_is_safe(version: str, classifiers: list[str], readme: str) -> Gate:
    if not _claims_v1(version):
        return Gate("version_claim_safety", True, "package is still pre-1.0")
    alpha = any("Alpha" in item for item in classifiers)
    unstable_readme = any(
        phrase in readme
        for phrase in (
            "no PyPI package release yet",
            "no GitHub release yet",
            "initial OSS implementation",
        )
    )
    passed = not alpha and not unstable_readme
    detail = (
        "v1 claim is not contradicted by metadata" if passed else "v1 metadata still says alpha"
    )
    return Gate("version_claim_safety", passed, detail)


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _function_body(source: str, name: str) -> str:
    pattern = re.compile(rf"^def {re.escape(name)}\(.*?(?=^def |\Z)", re.M | re.S)
    match = pattern.search(source)
    return match.group(0) if match else ""


def _claims_v1(version: str) -> bool:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return False
    major, minor, patch = (int(group) for group in match.groups())
    return (major, minor, patch) >= (1, 0, 0)


if __name__ == "__main__":
    sys.exit(main())
