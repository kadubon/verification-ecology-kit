"""All capacity CLI operations against a real atomic JSON ecology store."""

import json
from dataclasses import replace

from verification_ecology_kit.capacity.examples import scenario
from verification_ecology_kit.cli import main
from verification_ecology_kit.runtime.json_store import JsonStore


def test_capacity_cli(tmp_path, capsys):
    c, state = scenario("protected")
    contract = tmp_path / "contract.json"
    store = tmp_path / "ecology.json"
    contract.write_text(json.dumps(c.to_dict()), encoding="utf-8")
    JsonStore(store).save(state)
    base = [str(contract), "--store", str(store)]
    assert main(["capacity", "plan", *base]) == 0
    plan = json.loads(capsys.readouterr().out)
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    for command in ("check-plan", "apply-local"):
        extra = ["--event-id", "apply"] if command == "apply-local" else []
        assert main(["capacity", command, *base, "--plan", str(path), *extra]) == 0
        capsys.readouterr()
    for command in ("inspect", "replay", "compare"):
        assert main(["capacity", command, *base]) == 0
        capsys.readouterr()
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps({"event_id": "tick", "revision": 1, "kind": "tick", "payload": {"slot": 0}}),
        encoding="utf-8",
    )
    assert main(["capacity", "ingest", *base, "--event", str(event)]) == 0
    capsys.readouterr()
    for target in ("vek", "cait", "ccr"):
        assert (
            main(
                [
                    "capacity",
                    "export",
                    *base,
                    "--format",
                    target,
                    "--ccr-revision",
                    "1",
                    "--ccr-pool",
                    "p",
                    "--ccr-pool",
                    "b",
                ]
            )
            == 0
        )
        capsys.readouterr()
    assert main(["capacity", "example", "negative"]) == 0
    capsys.readouterr()


def test_capacity_cli_statuses(tmp_path, capsys):
    c, state = scenario("expiry")
    contract = tmp_path / "contract.json"
    store = tmp_path / "ecology.json"
    JsonStore(store).save(state)
    contract.write_text(json.dumps(c.to_dict()), encoding="utf-8")
    args = ["capacity", "plan", str(contract), "--store", str(store)]
    assert main(args) == 4
    capsys.readouterr()
    contract.write_text(json.dumps(replace(c, max_candidates=1).to_dict()), encoding="utf-8")
    assert main(args) == 3
    capsys.readouterr()
    contract.write_text("[]", encoding="utf-8")
    assert main(args) == 2
    capsys.readouterr()
