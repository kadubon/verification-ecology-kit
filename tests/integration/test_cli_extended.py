from __future__ import annotations

import json
from pathlib import Path

from verification_ecology_kit.cli import main
from verification_ecology_kit.model.packets import VerifierPacket


def _read(capsys) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def test_cli_validate_export_conformance_and_refs(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    packet_json = tmp_path / "packet.json"
    packet_json.write_text(json.dumps(VerifierPacket.minimal().to_dict()), encoding="utf-8")
    assert main(["validate", str(packet_json), "--schema", "verifier-packet.schema.json"]) == 0
    assert _read(capsys)["decision"] == "pass"

    assert main(["schema", "export", "--out", "schema-out"]) == 0
    assert "verifier-packet.schema.json" in _read(capsys)["exported"]

    bundle = tmp_path / "bundle.json"
    bundle.write_text(
        json.dumps(
            {
                "bundle_id": "b",
                "schema_version": "1",
                "conformance_profile": "core",
                "objects": [],
            }
        ),
        encoding="utf-8",
    )
    assert main(["conformance", str(bundle), "--profile", "core", "--format", "json"]) == 0
    assert _read(capsys)["decision"] == "accept"
    assert main(["refs", "check", str(bundle)]) == 0
    assert _read(capsys)["result"] == "pass"


def test_cli_ledger_packet_audits_runtime_and_scans(tmp_path: Path, capsys) -> None:
    ledger = tmp_path / "ledger.json"
    ledger.write_text('{"events": []}', encoding="utf-8")
    assert main(["ledger", "replay", str(ledger)]) == 0
    assert _read(capsys)["event_count"] == 0

    for operation in [
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
    ]:
        assert main(["packet", "operate", operation]) == 0
        assert _read(capsys)["operation"] == operation

    for audit in ["packet-ecology", "residual-metabolism", "adversarial-ingress", "monoculture"]:
        assert main(["audit", audit]) == 0
        assert "decision" in _read(capsys)

    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    before.write_text('{"question_form_capacity": {"feasible_capacity": 1}}', encoding="utf-8")
    after_payload = {
        "question_form_capacity": {
            "feasible_capacity": 1,
            "nominal_capacity": 1,
            "exercised_capacity": 1,
        }
    }
    after.write_text(
        json.dumps(after_payload),
        encoding="utf-8",
    )
    assert main(["audit", "aperture-regression", str(before), str(after)]) == 0
    assert _read(capsys)["decision"] == "pass"

    config = tmp_path / "config.json"
    config.write_text("{}", encoding="utf-8")
    assert main(["runtime", "run", str(config)]) == 0
    assert "generated_packets" in _read(capsys)

    assert main(["scan", "leaks", str(tmp_path)]) == 0
    assert _read(capsys)["decision"] == "pass"
    assert main(["scan", "local-info", str(tmp_path)]) == 0
    assert _read(capsys)["decision"] == "pass"
