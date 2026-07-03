"""Digest policies and deterministic hashing helpers."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from typing import Any

from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.errors import ErrorCode, VEKError
from verification_ecology_kit.result import CheckResult, FailureCode, fail_result, pass_result


@dataclass(frozen=True)
class Digest:
    algorithm_id: str
    value: str

    def to_dict(self) -> dict[str, str]:
        return {"algorithm_id": self.algorithm_id, "value": self.value}


@dataclass(frozen=True)
class DigestPolicy:
    policy_id: str = "vet-digest-policy-v1"
    default_algorithm: str = "sha256"
    accepted_algorithms: tuple[str, ...] = ("sha256",)
    collision_suspicion_policy: str = "quarantine"
    algorithm_deprecation_policy: str = "residualize"

    def validate_algorithm(self, algorithm_id: str) -> None:
        normalized = algorithm_id.lower()
        if normalized not in self.accepted_algorithms:
            raise VEKError(
                ErrorCode.UNSUPPORTED_DIGEST_ALGORITHM,
                "digest algorithm is not accepted by policy",
                details={"algorithm_id": algorithm_id},
            )

    def hash_bytes(self, data: bytes, *, algorithm_id: str | None = None) -> Digest:
        algorithm = (algorithm_id or self.default_algorithm).lower()
        self.validate_algorithm(algorithm)
        hasher = hashlib.new(algorithm)
        hasher.update(data)
        return Digest(algorithm_id=algorithm, value=hasher.hexdigest())

    def digest_json(
        self,
        value: Any,
        *,
        canonicalizer: Canonicalizer | None = None,
        algorithm_id: str | None = None,
    ) -> Digest:
        canon = canonicalizer or Canonicalizer()
        return self.hash_bytes(canon.canonicalize(value), algorithm_id=algorithm_id)


def object_digest_input(envelope: dict[str, Any]) -> dict[str, Any]:
    """Return the envelope form used for its own digest.

    The theory treats the envelope as the integrity unit. To avoid a circular hash, the
    digest value inside the top-level ``canonical_digest`` field is blanked before hashing.
    The algorithm identifier remains in the input so algorithm migration is visible.
    """

    prepared = copy.deepcopy(envelope)
    digest = prepared.get("canonical_digest")
    if isinstance(digest, dict):
        digest["value"] = ""
    return prepared


def check_record_digest(
    record: dict[str, Any],
    expected: Digest,
    *,
    policy: DigestPolicy | None = None,
    canonicalizer: Canonicalizer | None = None,
    check_name: str = "ObjectDigestOK",
) -> CheckResult:
    digest_policy = policy or DigestPolicy()
    try:
        actual = digest_policy.digest_json(
            record,
            canonicalizer=canonicalizer,
            algorithm_id=expected.algorithm_id,
        )
    except VEKError:
        return fail_result(check_name, FailureCode.CANONICALIZATION_DRIFT)
    if actual.value != expected.value:
        return fail_result(check_name, FailureCode.DIGEST_MISMATCH)
    return pass_result(check_name)
