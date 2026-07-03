"""Common record types and enumerations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
from typing import Any


class LifecycleStatus(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    REVOKED = "revoked"
    MIGRATED = "migrated"
    UNKNOWN = "unknown"


class LedgerStatus(StrEnum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    MERGED = "merged"
    RETIRED = "retired"
    REDACTED = "redacted"


class ResidualKind(StrEnum):
    UNRESOLVED = "unresolved"
    UNTRANSLATED = "untranslated"
    UNEXCLUDED = "unexcluded"
    MISSING = "missing"
    DELIBERATELY_PRESERVED = "deliberately_preserved"
    SCHEMA_OVERCLOSURE = "schema_overclosure"
    APERTURE_DEBT = "aperture_debt"
    LIVENESS_DEBT = "liveness_debt"
    SOUNDNESS_GAP = "soundness_gap"
    REDACTION_RESIDUAL = "redaction_residual"
    TRANSLATION_RESIDUAL = "translation_residual"
    MIGRATION_RESIDUAL = "migration_residual"
    CONFLICT_RESIDUAL = "conflict_residual"
    MISSING_COUNTER = "missing_counter"


class ResidualMetabolismRoute(StrEnum):
    QUESTION_FORMATION = "question_formation"
    COUNTEREXAMPLE_SEARCH = "counterexample_search"
    BOUNDARY_REVISION = "boundary_revision"
    TRANSLATION = "translation"
    PACKET_REPAIR = "packet_repair"
    PACKET_RETIREMENT = "packet_retirement"
    COUNTER_PACKET_GENERATION = "counter_packet_generation"
    SCHEMA_REVISION = "schema_revision"
    EXPLICIT_PRESERVED_UNKNOWN = "explicit_preserved_unknown"
    QUARANTINE = "quarantine"


class AuthorityAction(StrEnum):
    OBSERVATION = "observation"
    LOCAL_USE = "local_use"
    ARCHIVE = "archive"
    EXTERNAL_CIRCULATION = "external_circulation"
    INTERNALIZATION = "internalization"
    AUTOMATED_REPAIR = "automated_repair"
    RETIREMENT = "retirement"
    DEPLOYMENT = "deployment"
    SELF_MODIFICATION = "self_modification"
    FRONTIER_EXPANSION_CLAIM = "frontier_expansion_claim"


class AuthorityDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    QUARANTINE = "quarantine"
    RESIDUALIZE = "residualize"


class ConformanceProfile(StrEnum):
    CORE = "core"
    OPERATIONAL = "operational"
    FEDERATED = "federated"


class OriginKind(StrEnum):
    FAILURE = "failure"
    SUCCESS = "success"
    COUNTEREXAMPLE = "counterexample"
    RESIDUAL = "residual"
    CONTRAST = "contrast"
    EXTERNAL_PACKET = "external_packet"
    HUMAN_SPECIFICATION = "human_specification"


class Visibility(StrEnum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"
    REDACTED = "redacted"
    QUARANTINED = "quarantined"
    RETIRED = "retired"


class TrustStatus(StrEnum):
    LOCAL = "local"
    EXTERNAL_CANDIDATE = "external_candidate"
    LOW_TRUST = "low_trust"
    ADVERSARIAL = "adversarial"
    UNKNOWN = "unknown"


class ReachabilityMode(StrEnum):
    OVER = "over"
    UNDER = "under"
    SAMPLED = "sampled"
    MONITOR = "monitor"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TypeEnvironment:
    environment_id: str
    fields: dict[str, str]
    refinement_preorders: dict[str, str]
    translation_witnesses: dict[str, str]


@dataclass(frozen=True)
class TypedPartialRecord:
    type_environment_id: str
    fields: dict[str, Any]
    missing_type_residuals: tuple[str, ...] = ()

    def has_field(self, name: str) -> bool:
        return name in self.fields


@dataclass(frozen=True)
class ObservationSignature:
    signature_id: str
    type_environment: TypeEnvironment
    visible_fields: tuple[str, ...]
    carrier_registry_id: str
    projections: dict[str, str]
    redaction_requirements: tuple[str, ...] = ()
    provenance_requirements: tuple[str, ...] = ()
    comparison_requirements: tuple[str, ...] = ()
    information_preorder: str = "declared_by_policy"
    concretization_relation: str = "carrier_indexed"


def jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {key: jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list | set | frozenset):
        return [jsonable(item) for item in value]
    return value
