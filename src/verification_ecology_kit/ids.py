"""Identifier helpers."""

from __future__ import annotations

from uuid import uuid4

from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.digest import DigestPolicy


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def stable_id(prefix: str, value: object) -> str:
    digest = DigestPolicy().digest_json(value, canonicalizer=Canonicalizer())
    return f"{prefix}_{digest.value[:16]}"
