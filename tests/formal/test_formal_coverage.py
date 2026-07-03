from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _load_coverage_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_formal_coverage",
        ROOT / "scripts" / "check_formal_coverage.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_formal_coverage_gate_passes() -> None:
    script = _load_coverage_script()
    report = script.check_formal_coverage()
    assert report.decision == "pass", report.findings
    assert report.term_count >= len(script.REQUIRED_TERMS)


def test_required_formal_golden_traces_exist() -> None:
    expected = {
        "fork_preserves_lineage.json",
        "specialize_preserves_residuals.json",
        "generalize_boundary_aperture_obligation.json",
        "compose_boundary_counter_obligations.json",
        "repair_preserves_disposition.json",
        "retire_records_reinspection.json",
        "quarantine_records_recovery.json",
        "internalize_external_requires_pipeline.json",
        "redact_core_creates_residual.json",
        "authority_allow_requires_support_eligibility.json",
        "stale_support_blocks_authority.json",
        "non_live_soundgap_blocks_authority.json",
        "packet_spam_not_acceleration.json",
    }
    golden_root = ROOT / "tests" / "golden" / "formal_traces"
    actual = {path.name for path in golden_root.glob("*.json")}
    assert expected.issubset(actual)
