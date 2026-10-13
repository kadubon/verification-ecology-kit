"""Packaged fixtures, offline smoke, and schema-negative controls."""

import json
from importlib.resources import files

import pytest
from jsonschema import ValidationError

from verification_ecology_kit.capacity.examples import NAMES, scenario
from verification_ecology_kit.capacity.installed_check import run
from verification_ecology_kit.capacity.model import Contract, validate_schema


def test_offline_smoke_and_packaged_fixtures():
    report = run()
    assert report["offline"]
    root = files("verification_ecology_kit.capacity").joinpath("fixtures")
    for name in NAMES:
        data = json.loads(root.joinpath(f"{name}.json").read_text(encoding="utf-8"))
        assert Contract.from_dict(data) == scenario(name)[0]
    positive = json.loads(root.joinpath("report-positive.json").read_text(encoding="utf-8"))
    validate_schema("capacity-report", positive)
    negative = json.loads(root.joinpath("report-negative.json").read_text(encoding="utf-8"))
    with pytest.raises(ValidationError):
        validate_schema("capacity-report", negative)
