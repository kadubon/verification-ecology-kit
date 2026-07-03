"""Deterministic JSON canonicalization with strict interoperability checks."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from verification_ecology_kit.errors import ErrorCode, VEKError

JSONValue = None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]

IJSON_MIN_INT = -(2**53) + 1
IJSON_MAX_INT = 2**53 - 1


@dataclass(frozen=True)
class CanonicalizationPolicy:
    policy_id: str = "vet-json-canonicalization-v1"
    duplicate_member_policy: str = "fail"
    invalid_unicode_policy: str = "fail"
    non_interoperable_number_policy: str = "fail"
    sort_keys: bool = True
    ensure_ascii: bool = False


class Canonicalizer:
    """Canonicalizes JSON-compatible values for stable hashing.

    The implementation deliberately rejects duplicate object members during JSON parsing,
    surrogate Unicode code points, non-finite numbers, and integers outside the I-JSON
    interoperable range. Floats are accepted only when finite; deployments that require
    stricter JCS number formatting can set policy to fail before digest use.
    """

    def __init__(self, policy: CanonicalizationPolicy | None = None):
        self.policy = policy or CanonicalizationPolicy()

    def loads(self, text: str) -> JSONValue:
        def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            seen: set[str] = set()
            output: dict[str, Any] = {}
            for key, value in pairs:
                if key in seen:
                    raise VEKError(
                        ErrorCode.DUPLICATE_MEMBER,
                        f"duplicate JSON member: {key}",
                        details={"member": key},
                    )
                seen.add(key)
                output[key] = value
            return output

        loaded = json.loads(text, object_pairs_hook=pairs_hook, parse_float=Decimal)
        return self.prepare(loaded)

    def prepare(self, value: Any) -> JSONValue:
        return self._validate(value, path="$")

    def canonicalize(self, value: Any) -> bytes:
        prepared = self.prepare(value)
        text = json.dumps(
            prepared,
            sort_keys=self.policy.sort_keys,
            separators=(",", ":"),
            ensure_ascii=self.policy.ensure_ascii,
            allow_nan=False,
        )
        return text.encode("utf-8")

    def _validate(self, value: Any, *, path: str) -> JSONValue:
        if value is None or isinstance(value, bool):
            return value
        if isinstance(value, str):
            self._validate_string(value, path=path)
            return value
        if isinstance(value, int):
            if value < IJSON_MIN_INT or value > IJSON_MAX_INT:
                raise VEKError(
                    ErrorCode.NON_INTEROPERABLE_NUMBER,
                    "integer is outside the interoperable I-JSON range",
                    details={"path": path, "value": value},
                )
            return value
        if isinstance(value, Decimal):
            if not value.is_finite():
                raise VEKError(
                    ErrorCode.NON_INTEROPERABLE_NUMBER,
                    "non-finite decimal is not interoperable JSON",
                    details={"path": path},
                )
            as_float = float(value)
            if Decimal(str(as_float)) != value.normalize():
                raise VEKError(
                    ErrorCode.NON_INTEROPERABLE_NUMBER,
                    "decimal value cannot be represented deterministically as JSON number",
                    details={"path": path, "value": str(value)},
                )
            return as_float
        if isinstance(value, float):
            if not math.isfinite(value):
                raise VEKError(
                    ErrorCode.NON_INTEROPERABLE_NUMBER,
                    "non-finite float is not interoperable JSON",
                    details={"path": path},
                )
            return value
        if isinstance(value, list):
            return [
                self._validate(item, path=f"{path}/{index}") for index, item in enumerate(value)
            ]
        if isinstance(value, dict):
            output: dict[str, JSONValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise VEKError(
                        ErrorCode.SCHEMA_INVALID,
                        "JSON object keys must be strings",
                        details={"path": path, "key": repr(key)},
                    )
                self._validate_string(key, path=f"{path}/{key}")
                output[key] = self._validate(item, path=f"{path}/{key}")
            return output
        raise VEKError(
            ErrorCode.SCHEMA_INVALID,
            "value is not JSON-compatible",
            details={"path": path, "type": type(value).__name__},
        )

    def _validate_string(self, value: str, *, path: str) -> None:
        for char in value:
            code = ord(char)
            if 0xD800 <= code <= 0xDFFF:
                raise VEKError(
                    ErrorCode.INVALID_UNICODE,
                    "string contains an invalid Unicode surrogate code point",
                    details={"path": path},
                )
