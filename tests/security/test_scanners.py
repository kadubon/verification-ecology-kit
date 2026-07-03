from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

from verification_ecology_kit.audit.local_info import scan_local_info
from verification_ecology_kit.audit.security import (
    scan_secrets,
    verify_package_archives,
    verify_package_paths,
)


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


def test_package_content_script_requires_artifacts(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    report = verify_package_archives(dist)
    assert report.decision == "quarantine"
    assert "package_artifact_missing" in {finding.code for finding in report.findings}


def test_package_archive_scanner_requires_dist_directory(tmp_path: Path) -> None:
    report = verify_package_archives(tmp_path / "missing-dist")
    assert report.decision == "quarantine"
    assert len(report.findings) == 3


def test_package_archive_scanner_accepts_clean_artifacts(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    with zipfile.ZipFile(dist / "clean-1.0.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("clean/__init__.py", "")
    with tarfile.open(dist / "clean-1.0.0.tar.gz", "w:gz") as sdist:
        data = b"clean"
        info = tarfile.TarInfo("clean-1.0.0/README.md")
        info.size = len(data)
        sdist.addfile(info, io.BytesIO(data))

    report = verify_package_archives(dist)

    assert report.decision == "pass"
    assert len(report.evidence_refs) == 2


def test_package_archive_scanner_detects_forbidden_member(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    with zipfile.ZipFile(dist / "bad-1.0.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("bad/paper.aux", "")
    with tarfile.open(dist / "bad-1.0.0.tar.gz", "w:gz") as sdist:
        data = b"clean"
        info = tarfile.TarInfo("bad-1.0.0/README.md")
        info.size = len(data)
        sdist.addfile(info, io.BytesIO(data))

    report = verify_package_archives(dist)

    assert report.decision == "quarantine"
    assert "package_content_leak" in {finding.code for finding in report.findings}
