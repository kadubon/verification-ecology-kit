"""Local information leak scanner."""

from __future__ import annotations

import re
from pathlib import Path

from verification_ecology_kit.audit.allowlist import load_allowlist
from verification_ecology_kit.audit.reports import AuditFinding, AuditReport

LOCAL_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\\/\s]+", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^/\s]+", re.IGNORECASE),
)
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)


def scan_local_info(
    path: Path,
    *,
    allowlist: tuple[str, ...] = (),
    allowlist_path: Path | None = None,
) -> AuditReport:
    findings: list[AuditFinding] = []
    loaded = load_allowlist(allowlist_path)
    allowed_paths = allowlist + loaded.get("paths", ()) + loaded.get("local_info", ())
    allowed_emails = allowlist + loaded.get("emails", ())
    for file_path in _iter_text_files(path):
        if any(item in file_path.as_posix() for item in allowed_paths):
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for pattern in LOCAL_PATH_PATTERNS:
            for match in pattern.finditer(text):
                value = match.group(0)
                if any(item in value for item in allowed_paths):
                    continue
                findings.append(
                    AuditFinding(
                        "local_information_leak",
                        f"Local path-like value in {file_path.as_posix()}",
                        severity="high",
                    )
                )
        for match in EMAIL_PATTERN.finditer(text):
            value = match.group(0)
            if any(item in value for item in allowed_emails):
                continue
            findings.append(
                AuditFinding(
                    "private_email",
                    f"Email-like value in {file_path.as_posix()}",
                    severity="medium",
                )
            )
    return AuditReport(
        "local-info",
        "pass" if not findings else "quarantine",
        findings=findings,
        support_blocking_failures=["local_information_leak"] if findings else [],
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
