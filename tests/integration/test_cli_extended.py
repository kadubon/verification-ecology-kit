from __future__ import annotations

import json
from pathlib import Path

from verification_ecology_kit.cli import main
from verification_ecology_kit.model.packets import VerifierPacket


def _read(capsys) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def _operational_packet() -> VerifierPacket:
    packet = VerifierPacket.minimal()
    assert packet.boundary_refs is not None
    packet.boundary_refs.destructive_boundary_ref = "destructive-boundary"
    packet.boundary_refs.narrowing_boundary_ref = "narrowing-boundary"
    packet.counter_packet_refs.append("counter-packet-required")
    if packet.scope is not None:
        packet.scope.assumptions.append("declared-assumption")
    packet.question_form = {"kind": "fixture"}
    packet.extension["local"] = {"sensitive": "remove"}
    return packet


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


def test_cli_ledger_packet_audits_runtime_and_scans(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    ledger = tmp_path / "ledger.json"
    ledger.write_text('{"events": []}', encoding="utf-8")
    assert main(["ledger", "replay", str(ledger)]) == 0
    assert _read(capsys)["event_count"] == 0

    packet = tmp_path / "packet.json"
    packet.write_text(json.dumps(_operational_packet().to_dict()), encoding="utf-8")
    second_packet = tmp_path / "packet-2.json"
    second_packet.write_text(json.dumps(_operational_packet().to_dict()), encoding="utf-8")

    for operation in [
        "fork",
        "specialize",
        "generalize",
        "repair",
        "retire",
        "quarantine",
        "internalize",
        "redact",
    ]:
        out = tmp_path / f"{operation}.json"
        command = ["packet", "operate", operation, str(packet), "--out", str(out)]
        if operation == "redact":
            command.extend(["--field", "local"])
        if operation == "internalize":
            command.extend(["--translated", "true", "--boundary-checked", "true"])
        assert main(command) == 0
        result = _read(capsys)
        assert result["operation"] == operation
        assert out.exists()

    for operation in ["compose", "contrast"]:
        out = tmp_path / f"{operation}.json"
        assert (
            main(
                ["packet", "operate", operation, str(packet), str(second_packet), "--out", str(out)]
            )
            == 0
        )
        result = _read(capsys)
        assert result["operation"] == operation
        assert out.exists()

    audit_inputs = {
        "packet-ecology": packet,
        "residual-metabolism": ledger,
        "adversarial-ingress": packet,
        "monoculture": packet,
    }
    for audit, path in audit_inputs.items():
        assert main(["audit", audit, str(path)]) == 0
        assert "decision" in _read(capsys)

    schema_audit = tmp_path / "schema-overclosure.json"
    schema_audit.write_text('{"schema_rejected_unknown": true}', encoding="utf-8")
    assert main(["audit", "schema-overclosure", str(schema_audit)]) == 0
    assert _read(capsys)["decision"] == "residualize"

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
