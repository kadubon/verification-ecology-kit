from __future__ import annotations

import json
from pathlib import Path

from verification_ecology_kit.cli import main


def test_cli_doctor(capsys) -> None:
    assert main(["doctor"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["telemetry"] == "none"


def test_cli_packet_create(capsys) -> None:
    assert main(["packet", "create", "--template", "operational"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["counter_packet_refs"]


def test_cli_digest(tmp_path: Path, capsys) -> None:
    target = tmp_path / "object.json"
    target.write_text('{"a": 1}', encoding="utf-8")
    assert main(["digest", str(target)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["algorithm_id"] == "sha256"


def test_cli_schema_list(capsys) -> None:
    assert main(["schema", "list"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "verifier-packet.schema.json" in data["schemas"]


def test_cli_audit_schema_overclosure(capsys) -> None:
    assert main(["audit", "schema-overclosure"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["decision"] == "residualize"
