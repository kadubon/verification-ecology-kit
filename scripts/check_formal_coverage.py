"""Check the VET-Core formal coverage map."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TERMS = {
    "ObservableProcessHistory",
    "VerifierEcologyState",
    "VerifierPacket",
    "CoreAccountablePacket",
    "CounterPacket",
    "BoundaryTesterPacket",
    "ResidualRecord",
    "ResidualRoute",
    "ResidualLedger",
    "LedgerEvent",
    "TraceOK",
    "BoundaryRecord",
    "ReachabilityCertificate",
    "CounterexampleChannel",
    "SoundGapResidual",
    "CertificationRecord",
    "AuthorityDecision",
    "AuthInputs",
    "SupportReferenceResolver",
    "JValid",
    "Aperture",
    "Frontier",
    "OverclosureWitness",
    "SchemaOverclosureDetector",
    "LocalSovereignty",
    "LocalInternalizationPipeline",
    "RuntimeStep",
    "PacketOperation",
    "fork",
    "specialize",
    "generalize",
    "compose",
    "contrast",
    "repair",
    "retire",
    "quarantine",
    "internalize",
    "redact",
    "residual preservation theorem",
    "authority soundness theorem",
    "external packet non-authority theorem",
    "composition non-certification theorem",
    "packet spam theorem",
    "aperture debt theorem",
    "schema revisability theorem",
}

REQUIRED_FIELDS = (
    "theory_term",
    "formal_type",
    "formal_predicate",
    "operational_rule",
    "theorem",
    "python_module",
    "schema",
    "tests",
    "docs",
)


@dataclass(frozen=True)
class FormalCoverageReport:
    decision: str
    term_count: int
    findings: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(
            {
                "decision": self.decision,
                "term_count": self.term_count,
                "findings": list(self.findings),
            },
            indent=2,
            sort_keys=True,
        )


def check_formal_coverage(
    path: Path = ROOT / "tests" / "golden" / "formal_coverage.expected.json",
) -> FormalCoverageReport:
    findings: list[str] = []
    data = _load_json(path, findings)
    terms = data.get("terms") if isinstance(data, dict) else None
    if not isinstance(terms, list):
        return FormalCoverageReport("fail", 0, ("terms must be a list",))

    lean_text = _lean_text()
    seen_terms: set[str] = set()
    for index, row in enumerate(terms):
        if not isinstance(row, dict):
            findings.append(f"row {index} is not an object")
            continue
        term = str(row.get("theory_term", "")).strip()
        seen_terms.add(term)
        for field_name in REQUIRED_FIELDS:
            if not str(row.get(field_name, "")).strip():
                findings.append(f"{term or index}: missing {field_name}")
        if row.get("theorem") != "not_applicable":
            theorem = str(row.get("theorem", "")).strip()
            if theorem and theorem not in lean_text:
                findings.append(f"{term}: theorem not found in Lean files: {theorem}")
        formal_type = _lean_symbol(str(row.get("formal_type", "")))
        if formal_type and formal_type not in lean_text:
            findings.append(f"{term}: formal type not found in Lean files: {formal_type}")
        formal_predicate = _lean_symbol(str(row.get("formal_predicate", "")))
        if formal_predicate and formal_predicate not in lean_text:
            findings.append(f"{term}: formal predicate not found in Lean files: {formal_predicate}")
        operational_rule = _lean_symbol(str(row.get("operational_rule", "")))
        if operational_rule and operational_rule not in lean_text:
            findings.append(f"{term}: operational rule not found in Lean files: {operational_rule}")
        _check_existing_path("docs", row, findings)
        _check_existing_path("tests", row, findings)
        schema = str(row.get("schema", "")).strip()
        if (
            schema
            and not (ROOT / "src" / "verification_ecology_kit" / "schemas" / schema).is_file()
        ):
            findings.append(f"{term}: schema file is missing: {schema}")

    missing_terms = sorted(REQUIRED_TERMS - seen_terms)
    for term in missing_terms:
        findings.append(f"required term is missing: {term}")

    return FormalCoverageReport(
        decision="pass" if not findings else "fail",
        term_count=len(terms),
        findings=tuple(findings),
    )


def main() -> int:
    report = check_formal_coverage()
    print(report.to_json())
    return 0 if report.decision == "pass" else 1


def _load_json(path: Path, findings: list[str]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(f"coverage file is missing: {path}")
    except json.JSONDecodeError as exc:
        findings.append(f"coverage file is invalid JSON: {exc}")
    return {}


def _lean_text() -> str:
    root = ROOT / "formal" / "lean" / "VETCore"
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(root.glob("*.lean")))


def _lean_symbol(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    return value.split(".")[-1]


def _check_existing_path(kind: str, row: dict[str, Any], findings: list[str]) -> None:
    raw_path = str(row.get(kind, "")).strip()
    term = str(row.get("theory_term", "<unknown>"))
    if raw_path and not (ROOT / raw_path).is_file():
        findings.append(f"{term}: {kind} file is missing: {raw_path}")


if __name__ == "__main__":
    sys.exit(main())
