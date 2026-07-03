"""Allowlist loading for local audit scanners."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


def load_allowlist(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    candidate = path or ROOT / "security" / "allowlist.toml"
    if not candidate.exists():
        return {}
    with candidate.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        return {}
    secrets = _table(data.get("secrets"))
    return {
        "local_info": _strings(data, "local_info"),
        "emails": _strings(data, "emails"),
        "paths": _strings(data, "paths") + _strings(secrets, "paths"),
        "secret_values": _strings(secrets, "values"),
        "secret_regexes": _strings(secrets, "regexes"),
    }


def _table(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strings(table: dict[str, Any], key: str) -> tuple[str, ...]:
    value = table.get(key, ())
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value if str(item))
