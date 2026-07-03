"""Check that formal-semantics claims match the release gates."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALLOWED_CLAIM = (
    "verification-ecology-kit provides a complete formal operational semantics "
    "for the VET-Core implemented by this package, with machine-checked safety "
    "theorems and Python conformance tests against the formal semantics."
)

REQUIRED_FORMAL_FILES = (
    "formal/README.md",
    "formal/CLAIMS.md",
    "formal/lean/lakefile.lean",
    "formal/lean/lean-toolchain",
    "formal/lean/VETCore/Syntax.lean",
    "formal/lean/VETCore/WellFormed.lean",
    "formal/lean/VETCore/Semantics.lean",
    "formal/lean/VETCore/Invariants.lean",
    "formal/lean/VETCore/Authority.lean",
    "formal/lean/VETCore/Residual.lean",
    "formal/lean/VETCore/Aperture.lean",
    "formal/lean/VETCore/Runtime.lean",
    "formal/lean/VETCore/Theorems.lean",
    "formal/lean/VETCore/Examples.lean",
    "docs/formal_semantics.md",
    "docs/formal_claims.md",
    "docs/semantic_boundary.md",
    "tests/golden/formal_coverage.expected.json",
    "scripts/check_formal_coverage.py",
    "scripts/check_formal_claims.py",
)

REQUIRED_THEOREMS = (
    "residual_preservation_step",
    "active_residual_without_live_route_blocks_authority",
    "admissible_operation_preserves_or_residualizes_invariants",
    "compose_not_automatically_certified",
    "redaction_requires_residual",
    "generalization_requires_boundary_work",
    "authority_allow_requires_support_eligibility",
    "stale_revoked_unknown_support_blocks_authority",
    "migrated_support_requires_witness",
    "external_packet_not_authority_before_internalization",
    "runtime_preserves_ecological_invariants",
    "packet_spam_not_acceleration",
    "aperture_loss_requires_debt",
    "missing_schema_field_can_residualize",
    "anti_overclosure_overclosure_blocked",
)

FORBIDDEN_CLAIMS = (
    "proves Verifier Ecology Theory",
    "fully verifies all Python code",
    "proves AI safety",
    "complete mathematical theory of self-improving intelligence",
    "universal verifier correctness",
    "Python implementation is fully formally verified",
)


@dataclass(frozen=True)
class FormalClaimsReport:
    decision: str
    version: str
    allowed_claim: str
    theorem_count: int
    findings: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(
            {
                "decision": self.decision,
                "version": self.version,
                "allowed_claim": self.allowed_claim,
                "theorem_count": self.theorem_count,
                "findings": list(self.findings),
            },
            indent=2,
            sort_keys=True,
        )


def check_formal_claims() -> FormalClaimsReport:
    findings: list[str] = []
    pyproject = _read_pyproject()
    version = str(pyproject["project"]["version"])
    if _version_tuple(version) < (1, 2, 0):
        findings.append(f"version must be at least 1.2.0 for the formal VET-Core claim: {version}")

    for path in REQUIRED_FORMAL_FILES:
        if not (ROOT / path).is_file():
            findings.append(f"required file is missing: {path}")

    lean_files = sorted((ROOT / "formal" / "lean" / "VETCore").glob("*.lean"))
    lean_text = "\n".join(path.read_text(encoding="utf-8") for path in lean_files)
    for term in ("sorry", "admit"):
        if re.search(term, lean_text):
            findings.append(f"Lean source contains blocked proof token: {term}")
    for theorem in REQUIRED_THEOREMS:
        if f"theorem {theorem}" not in lean_text:
            findings.append(f"required theorem is missing: {theorem}")

    claim_targets = ("README.md", "docs/formal_claims.md", "docs/formal_semantics.md")
    for target in claim_targets:
        text = _read_text(target)
        if ALLOWED_CLAIM not in _normalize_space(text):
            findings.append(f"allowed claim text is missing from {target}")

    boundary_text = _normalize_space(
        _read_text("docs/semantic_boundary.md") + "\n" + _read_text("README.md")
    )
    if (
        "Python implementation is conformance-tested against the formal VET-Core semantics"
        not in boundary_text
    ):
        findings.append("Python conformance-test boundary is missing")
    if "not fully formally verified" not in boundary_text:
        findings.append("Python formal-verification limit is missing")

    scanned = "\n".join(
        _read_text(path)
        for path in (
            "README.md",
            "docs/formal_claims.md",
            "docs/formal_semantics.md",
            "docs/semantic_boundary.md",
        )
    )
    for phrase in FORBIDDEN_CLAIMS:
        if phrase in scanned:
            findings.append(f"forbidden claim appears in docs: {phrase}")

    return FormalClaimsReport(
        decision="pass" if not findings else "fail",
        version=version,
        allowed_claim=ALLOWED_CLAIM,
        theorem_count=len(REQUIRED_THEOREMS),
        findings=tuple(findings),
    )


def main() -> int:
    report = check_formal_claims()
    print(report.to_json())
    return 0 if report.decision == "pass" else 1


def _read_pyproject() -> dict[str, object]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return data


def _version_tuple(version: str) -> tuple[int, int, int]:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        return (0, 0, 0)
    return tuple(int(group) for group in match.groups())


def _read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _normalize_space(text: str) -> str:
    return " ".join(text.split())


if __name__ == "__main__":
    sys.exit(main())
