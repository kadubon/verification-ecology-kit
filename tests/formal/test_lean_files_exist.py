from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_lean_formalization_files_exist_and_have_no_blocked_tokens() -> None:
    required = [
        "Syntax.lean",
        "WellFormed.lean",
        "Semantics.lean",
        "Invariants.lean",
        "Authority.lean",
        "Residual.lean",
        "Aperture.lean",
        "Runtime.lean",
        "Theorems.lean",
        "Examples.lean",
    ]
    lean_root = ROOT / "formal" / "lean" / "VETCore"
    for name in required:
        path = lean_root / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert "sorry" not in text
        assert "admit" not in text


def test_lean_toolchain_and_lakefile_exist() -> None:
    assert (ROOT / "formal" / "lean" / "lean-toolchain").is_file()
    assert (ROOT / "formal" / "lean" / "lakefile.lean").is_file()
