from __future__ import annotations

from pathlib import Path

ROWS = [
    (
        "ObservableProcessHistory",
        "model/history.py",
        "vet-bundle.schema.json",
        "tests/unit/test_history_ledger.py",
        "docs/data_model.md",
    ),
    (
        "VerifierPacket",
        "model/packets.py",
        "verifier-packet.schema.json",
        "tests/unit/test_packets_operations.py",
        "docs/concepts.md",
    ),
    (
        "ResidualLedger",
        "model/ledger.py",
        "residual-ledger.schema.json",
        "tests/unit/test_history_ledger.py",
        "docs/data_model.md",
    ),
    (
        "ConformanceAlgorithm",
        "model/conformance.py",
        "conformance-report.schema.json",
        "tests/unit/test_conformance_authority.py",
        "docs/conformance.md",
    ),
    (
        "AuthorityDecision",
        "model/authority.py",
        "authority-decision.schema.json",
        "tests/unit/test_conformance_authority.py",
        "docs/conformance.md",
    ),
    (
        "OverclosureWitness",
        "model/overclosure.py",
        "residual-record.schema.json",
        "tests/unit/test_audits_runtime.py",
        "docs/audits.md",
    ),
]


def main() -> int:
    lines = [
        "# Theory Mapping",
        "",
        "| Theory term | Module | JSON schema | Tests | Docs |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in ROWS:
        lines.append("| " + " | ".join(row) + " |")
    Path("docs/theory_mapping.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
