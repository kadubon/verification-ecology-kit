"""Secret and package safety scanners."""

from __future__ import annotations

import re
import tarfile
import zipfile
from pathlib import Path

from verification_ecology_kit.audit.allowlist import load_allowlist
from verification_ecology_kit.audit.reports import AuditFinding, AuditReport

TOKEN_PREFIXES = ("sk" + "-", "gh" + "p_", "gh" + "o_", "pypi" + "-")
PRIVATE_KEY_MARKER = "BEGIN " + "PRIVATE KEY"
AWS_ACCESS_KEY = "AK" + "IA"
TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "token",
        re.compile(
            "(" + "|".join(re.escape(prefix) for prefix in TOKEN_PREFIXES) + r")[A-Za-z0-9_\-]{12,}"
        ),
    ),
    ("github_pat", re.compile(r"(github" + r"_pat_)[A-Za-z0-9_]{22,}")),
    ("github_token", re.compile(r"(gh" + r"[usro]_[A-Za-z0-9_]{16,})")),
    ("npm_token", re.compile(r"(npm" + r"_[A-Za-z0-9_\-]{20,})")),
    ("slack_token", re.compile(r"(xox" + r"[abprs]-[A-Za-z0-9\-]{20,})")),
    ("google_api_key", re.compile(r"(AI" + r"za[0-9A-Za-z_\-]{20,})")),
    ("cloud_credential", re.compile(r"((?:AK" + r"IA|ASIA)[A-Z0-9]{16})")),
)


def scan_secrets(
    path: Path,
    *,
    allowlist_path: Path | None = None,
    allowlist: dict[str, tuple[str, ...]] | None = None,
) -> AuditReport:
    findings: list[AuditFinding] = []
    allow = allowlist or load_allowlist(allowlist_path)
    allowed_paths = allow.get("paths", ())
    allowed_values = allow.get("secret_values", ())
    allowed_regexes = tuple(re.compile(pattern) for pattern in allow.get("secret_regexes", ()))
    for file_path in _iter_text_files(path):
        if _path_allowed(file_path, allowed_paths):
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if PRIVATE_KEY_MARKER in text:
            findings.append(
                AuditFinding("private_key", f"Private key marker in {file_path.as_posix()}", "high")
            )
        for code, pattern in TOKEN_PATTERNS:
            for match in pattern.finditer(text):
                value = match.group(0)
                if _value_allowed(value, allowed_values, allowed_regexes):
                    continue
                findings.append(
                    AuditFinding(
                        code,
                        f"{_redacted(value)} in {file_path.as_posix()}",
                        "high",
                        evidence_refs=(file_path.as_posix(),),
                    )
                )
        if file_path.name.startswith(".env") and file_path.name != ".env.example":
            findings.append(
                AuditFinding(
                    "env_file", f"Environment file included: {file_path.as_posix()}", "high"
                )
            )
    return AuditReport(
        "security",
        "pass" if not findings else "quarantine",
        findings=findings,
        support_blocking_failures=["secret_leak"] if findings else [],
    ).finalize()


def _path_allowed(file_path: Path, allowed_paths: tuple[str, ...]) -> bool:
    path_text = file_path.as_posix()
    return any(item in path_text for item in allowed_paths)


def _value_allowed(
    value: str,
    allowed_values: tuple[str, ...],
    allowed_regexes: tuple[re.Pattern[str], ...],
) -> bool:
    return value in allowed_values or any(pattern.search(value) for pattern in allowed_regexes)


def _redacted(value: str) -> str:
    prefix = value.split("-", 1)[0] if "-" in value else value[:4]
    return f"{prefix}[redacted]"


def verify_package_paths(paths: list[Path]) -> AuditReport:
    findings: list[AuditFinding] = []
    forbidden_suffixes = {".aux", ".bbl", ".bcf", ".blg", ".log", ".out", ".toc", ".pdf"}
    for path in paths:
        if path.suffix.lower() in forbidden_suffixes:
            findings.append(
                AuditFinding(
                    "package_content_leak", f"Forbidden build artifact: {path.as_posix()}", "high"
                )
            )
        if ".ipynb_checkpoints" in path.parts:
            findings.append(
                AuditFinding(
                    "package_content_leak", f"Notebook checkpoint: {path.as_posix()}", "high"
                )
            )
    return AuditReport(
        "package-contents",
        "pass" if not findings else "quarantine",
        findings=findings,
        support_blocking_failures=["package_content_leak"] if findings else [],
    ).finalize()


def verify_package_archives(dist: Path) -> AuditReport:
    findings: list[AuditFinding] = []
    paths: list[Path] = []
    evidence_refs: list[str] = []
    wheels = 0
    sdists = 0

    if not dist.exists():
        findings.append(
            AuditFinding("package_artifact_missing", "dist directory is missing", "high")
        )
    else:
        for archive in dist.iterdir():
            if archive.suffix == ".whl":
                wheels += 1
                evidence_refs.append(archive.as_posix())
                with zipfile.ZipFile(archive) as wheel:
                    paths.extend(Path(name) for name in wheel.namelist())
            elif archive.suffixes[-2:] == [".tar", ".gz"]:
                sdists += 1
                evidence_refs.append(archive.as_posix())
                with tarfile.open(archive) as sdist:
                    paths.extend(Path(member.name) for member in sdist.getmembers())

    if wheels == 0:
        findings.append(
            AuditFinding("package_artifact_missing", "wheel artifact is missing", "high")
        )
    if sdists == 0:
        findings.append(
            AuditFinding("package_artifact_missing", "sdist artifact is missing", "high")
        )

    content_report = verify_package_paths(paths)
    findings.extend(content_report.findings)
    return AuditReport(
        "package-contents",
        "pass" if not findings else "quarantine",
        findings=findings,
        support_blocking_failures=["package_content_leak"] if findings else [],
        evidence_refs=evidence_refs,
    ).finalize()


def _iter_text_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    excluded = {
        ".git",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".hypothesis",
        "__pycache__",
        "dist",
        "build",
        "site",
    }
    files: list[Path] = []
    for file_path in path.rglob("*"):
        if any(part in excluded for part in file_path.parts):
            continue
        if file_path.name == ".coverage":
            continue
        if file_path.is_file() and file_path.suffix.lower() not in {
            ".pyc",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".pdf",
        }:
            files.append(file_path)
    return files
