"""Check whether the repository is allowed to claim v1.0.0 readiness."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

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
        help="Fail if any readiness gap remains, even before version 1.0.0.",
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
        _gate_no_placeholder_terms(),
        _gate_changelog_v1(changelog),
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
    required = ("Do not bump", "1.0.0", "scripts/check_v1_readiness.py --strict")
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
