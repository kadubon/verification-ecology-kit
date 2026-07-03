"""Structured exceptions and stable error codes."""

from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    SCHEMA_INVALID = "schema_invalid"
    DUPLICATE_MEMBER = "duplicate_member"
    INVALID_UNICODE = "invalid_unicode"
    NON_INTEROPERABLE_NUMBER = "non_interoperable_number"
    UNSUPPORTED_DIGEST_ALGORITHM = "unsupported_digest_algorithm"
    DIGEST_MISMATCH = "digest_mismatch"
    CANONICALIZATION_DRIFT = "canonicalization_drift"
    UNRESOLVED_REFERENCE = "unresolved_reference"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    PATH_TRAVERSAL = "path_traversal"
    STATUS_BLOCKS_SUPPORT = "status_blocks_support"
    JUDGMENT_INVALID = "judgment_invalid"
    RESIDUAL_NOT_LIVE = "residual_not_live"
    SOUNDGAP_NOT_LIVE = "soundgap_not_live"
    AUTHORITY_MISMATCH = "authority_mismatch"
    POLICY_VIOLATION = "policy_violation"


class VEKError(Exception):
    """Base exception with a machine-readable code."""

    def __init__(self, code: ErrorCode, message: str, *, details: dict[str, object] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, object]:
        return {"code": self.code.value, "message": self.message, "details": self.details}
