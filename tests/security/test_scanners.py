from __future__ import annotations

from pathlib import Path

from verification_ecology_kit.audit.local_info import scan_local_info
from verification_ecology_kit.audit.security import scan_secrets, verify_package_paths


def test_secret_scanner_detects_token_like_value(tmp_path: Path) -> None:
    target = tmp_path / "secret.txt"
    target.write_text("sk-" + "a" * 20, encoding="utf-8")
    report = scan_secrets(tmp_path)
    assert report.decision == "quarantine"


def test_local_info_scanner_detects_local_path(tmp_path: Path) -> None:
    target = tmp_path / "path.txt"
    target.write_text("C:" + "\\Users\\name\\file.txt", encoding="utf-8")
    report = scan_local_info(tmp_path)
    assert report.decision == "quarantine"


def test_package_content_scanner_detects_tex_artifact() -> None:
    report = verify_package_paths([Path("paper.aux")])
    assert report.decision == "quarantine"
