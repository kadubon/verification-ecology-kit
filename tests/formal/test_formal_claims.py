from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _load_claims_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_formal_claims",
        ROOT / "scripts" / "check_formal_claims.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_formal_claim_gate_passes() -> None:
    script = _load_claims_script()
    report = script.check_formal_claims()
    assert report.decision == "pass", report.findings
    assert report.version == "1.2.0"
    assert report.theorem_count == len(script.REQUIRED_THEOREMS)
