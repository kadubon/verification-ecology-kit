from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE_FIXTURE = ROOT / "tests" / "golden" / "theory_coverage.expected.json"
OUTPUT = ROOT / "docs" / "theory_mapping.md"

PLAIN_WORDING = {
    "VerifierPacket": "verifier packet",
    "ResidualLedger": "residual ledger",
    "Aperture": "aperture",
    "VerifierMonocultureDetector": "monoculture",
    "SchemaOverclosureDetector": "schema overclosure",
    "OverclosureWitness": "overclosure witness",
    "AuthorityDecision": "authority decision",
    "ConformanceEngine": "conformance engine",
    "VetBundle": "bundle",
    "ObjectRef": "object reference",
    "DigestRecord": "digest record",
}


def _plain_wording(theory_term: str) -> str:
    if theory_term in PLAIN_WORDING:
        return PLAIN_WORDING[theory_term]
    words: list[str] = []
    current = ""
    for char in theory_term.replace("/", " ").replace("-", " "):
        if char.isupper() and current and current[-1].islower():
            words.append(current)
            current = char.lower()
        elif char.isspace():
            if current:
                words.append(current)
                current = ""
        else:
            current += char.lower()
    if current:
        words.append(current)
    return " ".join(words)


def main() -> int:
    data = json.loads(COVERAGE_FIXTURE.read_text(encoding="utf-8"))
    terms = data["terms"]
    lines = [
        "# Theory Mapping",
        "",
        "This page maps Verifier Ecology Theory terms to the package artifacts that",
        "implement their operational checks. The fuller v1 audit matrix is in",
        "[V1 Audit](v1_audit.md).",
        "",
        "| Theory term | Plain wording | Module | JSON schema | Tests | Docs | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in terms:
        theory_term = str(item["theory_term"])
        tests = ", ".join(str(test) for test in item["tests"])
        row = (
            theory_term,
            _plain_wording(theory_term),
            str(item["module"]),
            str(item["schema"]),
            tests,
            str(item["docs"]),
            str(item["status"]),
        )
        lines.append("| " + " | ".join(row) + " |")
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
