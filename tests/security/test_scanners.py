from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

from verification_ecology_kit.audit.allowlist import load_allowlist
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
    assert "a" * 20 not in report.to_json()


def test_secret_scanner_uses_toml_allowlist(tmp_path: Path) -> None:
    target = tmp_path / "secret.txt"
    token = "github_pat_" + "A" * 30
    target.write_text(token, encoding="utf-8")
    allowlist = tmp_path / "allowlist.toml"
    allowlist.write_text(
        '[secrets]\nvalues = ["' + token + '"]\nregexes = []\npaths = []\n',
        encoding="utf-8",
    )
    report = scan_secrets(tmp_path, allowlist_path=allowlist)
    assert report.decision == "pass"


def test_secret_scanner_redacts_jwt_and_high_entropy_values(tmp_path: Path) -> None:
    jwt = "eyJ" + "A" * 20 + "." + "B" * 20 + "." + "C" * 20
    entropy_value = "A9zY8xW7vU6tS5rQ4pO3nM2lK1jI0hGfEdCb"
    target = tmp_path / "tokens.txt"
    target.write_text(f"{jwt}\n{entropy_value}\n", encoding="utf-8")

    report = scan_secrets(tmp_path)
    rendered = report.to_json()

    assert report.decision == "quarantine"
    assert jwt not in rendered
    assert entropy_value not in rendered


def test_secret_scanner_ignores_lock_hashes_and_test_entropy_fixtures(tmp_path: Path) -> None:
    entropy_value = "A9zY8xW7vU6tS5rQ4pO3nM2lK1jI0hGfEdCb"
    (tmp_path / "uv.lock").write_text(
        f"https://files.pythonhosted.org/packages/aa/bb/{entropy_value}/pkg.whl\n",
        encoding="utf-8",
    )
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "fixture.py").write_text(f'TOKEN = "{entropy_value}"\n', encoding="utf-8")

    report = scan_secrets(tmp_path)

    assert report.decision == "pass"


def test_allowlist_loader_and_scanners_handle_paths_and_regexes(tmp_path: Path) -> None:
    assert load_allowlist(tmp_path / "missing.toml") == {}

    target = tmp_path / "allowed" / "secret.txt"
    target.parent.mkdir()
    target.write_text("npm_" + "A" * 30, encoding="utf-8")
    allowlist = tmp_path / "allowlist.toml"
    allowlist.write_text(
        'local_info = "bad"\n'
        "emails = []\n"
        'paths = ["allowed"]\n'
        "\n"
        "[secrets]\n"
        "values = []\n"
        'regexes = ["^npm_"]\n'
        "paths = []\n",
        encoding="utf-8",
    )

    loaded = load_allowlist(allowlist)

    assert loaded["local_info"] == ()
    assert scan_secrets(tmp_path, allowlist_path=allowlist).decision == "pass"
    assert scan_local_info(tmp_path, allowlist_path=allowlist).decision == "pass"


def test_local_info_scanner_detects_local_path(tmp_path: Path) -> None:
    target = tmp_path / "path.txt"
    target.write_text("C:" + "\\Users\\name\\file.txt", encoding="utf-8")
    report = scan_local_info(tmp_path)
    assert report.decision == "quarantine"


def test_package_content_scanner_detects_tex_artifact() -> None:
    report = verify_package_paths([Path("paper.aux")])
    assert report.decision == "quarantine"


def test_package_content_scanner_detects_local_absolute_path() -> None:
    report = verify_package_paths([Path("C:" + "/" + "Users" + "/name/project/private.txt")])
    assert report.decision == "quarantine"
    assert "local_path_leak" in {finding.code for finding in report.findings}


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


def test_package_archive_scanner_detects_local_absolute_path_in_content(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    with zipfile.ZipFile(dist / "bad-1.0.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr(
            "bad/__init__.py",
            "ROOT = '" + "C:" + "/" + "Users" + "/name/project'\n",
        )
    with tarfile.open(dist / "bad-1.0.0.tar.gz", "w:gz") as sdist:
        data = b"clean"
        info = tarfile.TarInfo("bad-1.0.0/README.md")
        info.size = len(data)
        sdist.addfile(info, io.BytesIO(data))

    report = verify_package_archives(dist)

    assert report.decision == "quarantine"
    assert "local_path_leak" in {finding.code for finding in report.findings}
