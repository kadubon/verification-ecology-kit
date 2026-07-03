"""Secret and package safety scanners."""

from __future__ import annotations

import re
from pathlib import Path

from verification_ecology_kit.audit.reports import AuditFinding, AuditReport

TOKEN_PREFIXES = ("sk" + "-", "gh" + "p_", "gh" + "o_", "pypi" + "-")
PRIVATE_KEY_MARKER = "BEGIN " + "PRIVATE KEY"
AWS_ACCESS_KEY = "AK" + "IA"


def scan_secrets(path: Path) -> AuditReport:
    findings: list[AuditFinding] = []
    token_pattern = re.compile(
        "(" + "|".join(re.escape(prefix) for prefix in TOKEN_PREFIXES) + r")[A-Za-z0-9_\-]{12,}"
    )
    for file_path in _iter_text_files(path):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if PRIVATE_KEY_MARKER in text:
            findings.append(
                AuditFinding("private_key", f"Private key marker in {file_path.as_posix()}", "high")
            )
        if AWS_ACCESS_KEY in text:
            findings.append(
                AuditFinding(
                    "cloud_credential", f"Cloud key marker in {file_path.as_posix()}", "high"
                )
            )
        if token_pattern.search(text):
            findings.append(
                AuditFinding("token", f"Token-like value in {file_path.as_posix()}", "high")
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
