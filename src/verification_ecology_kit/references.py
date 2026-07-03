"""Object envelopes, references, schema catalogues, and JSON Pointer resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from verification_ecology_kit.digest import Digest, DigestPolicy, object_digest_input
from verification_ecology_kit.errors import ErrorCode, VEKError
from verification_ecology_kit.model.lifecycle import StatusEvent, StatusFold, StatusView
from verification_ecology_kit.model.records import LifecycleStatus, jsonable
from verification_ecology_kit.result import (
    CheckResult,
    FailureCode,
    fail_result,
    pass_result,
    residual_result,
)


@dataclass(frozen=True)
class ObjectRef:
    bundle_id: str
    object_id: str
    schema_id: str
    pointer: str = ""
    digest_algorithm_id: str = "sha256"
    digest: Digest | None = None
    intended_use: str = "support"

    def to_dict(self) -> dict[str, object]:
        return {
            "bundle_id": self.bundle_id,
            "object_id": self.object_id,
            "schema_id": self.schema_id,
            "pointer": self.pointer,
            "digest_algorithm_id": self.digest_algorithm_id,
            "digest": self.digest.to_dict()
            if self.digest
            else {"algorithm_id": "sha256", "value": ""},
            "intended_use": self.intended_use,
        }


@dataclass
class ObjectEnvelope:
    object_id: str
    schema_id: str
    schema_version: str
    payload: dict[str, Any]
    canonical_digest: Digest = field(default_factory=lambda: Digest("sha256", ""))
    status_ref: ObjectRef | None = None
    provenance: list[str] = field(default_factory=list)
    residual_refs: list[ObjectRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "object_id": self.object_id,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "canonical_digest": self.canonical_digest.to_dict(),
            "status_ref": self.status_ref.to_dict() if self.status_ref else None,
            "provenance": self.provenance,
            "residual_refs": [ref.to_dict() for ref in self.residual_refs],
            "payload": self.payload,
        }

    def refresh_digest(self, policy: DigestPolicy | None = None) -> Digest:
        digest_policy = policy or DigestPolicy()
        self.canonical_digest = digest_policy.digest_json(object_digest_input(self.to_dict()))
        return self.canonical_digest

    def ref(self, *, bundle_id: str, pointer: str = "", intended_use: str = "support") -> ObjectRef:
        return ObjectRef(
            bundle_id=bundle_id,
            object_id=self.object_id,
            schema_id=self.schema_id,
            pointer=pointer,
            digest_algorithm_id=self.canonical_digest.algorithm_id,
            digest=self.canonical_digest,
            intended_use=intended_use,
        )


@dataclass(frozen=True)
class ReferenceEdge:
    reference_id: str
    from_object_ref: ObjectRef
    pointer: str
    target_schema: str
    target_id: str
    target_digest: Digest | None
    intended_use: str
    residual_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


@dataclass(frozen=True)
class DigestRecord:
    digest_record_id: str
    object_ref: ObjectRef
    schema_version: str
    canonicalization_policy_id: str
    digest_policy_id: str
    digest_algorithm_id: str
    canonical_digest: Digest
    object_digest_ok_judgment_ref: str = ""
    collision_suspicion: bool = False
    algorithm_deprecated: bool = False
    canonicalization_drift: bool = False
    residual_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "digest_record_id": self.digest_record_id,
            "object_ref": self.object_ref.to_dict(),
            "schema_version": self.schema_version,
            "canonicalization_policy_id": self.canonicalization_policy_id,
            "digest_policy_id": self.digest_policy_id,
            "digest_algorithm_id": self.digest_algorithm_id,
            "canonical_digest": self.canonical_digest.to_dict(),
            "ObjectDigestOK_judgment_ref": self.object_digest_ok_judgment_ref,
            "collision_suspicion": self.collision_suspicion,
            "algorithm_deprecated": self.algorithm_deprecated,
            "canonicalization_drift": self.canonicalization_drift,
            "residual_refs": list(self.residual_refs),
        }


@dataclass(frozen=True)
class SchemaMigrationWitness:
    migration_witness_id: str
    from_schema_version: str
    to_schema_version: str
    field_mapping_ref: ObjectRef
    transformed_object_ref: ObjectRef
    source_digest: Digest
    target_digest: Digest
    loss_residual_refs: tuple[str, ...]
    migration_judgment_ref: str
    status: str = "active"

    def preserves_or_residualizes_loss(self) -> bool:
        return bool(self.migration_judgment_ref) and (
            self.source_digest.value == self.target_digest.value or bool(self.loss_residual_refs)
        )

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


@dataclass
class SchemaCatalogue:
    catalogue_id: str
    accepted_schema_versions: dict[str, tuple[str, ...]]
    schemas: dict[str, dict[str, Any]] = field(default_factory=dict)
    migration_witnesses: dict[tuple[str, str], str] = field(default_factory=dict)

    def accepts(self, schema_id: str, schema_version: str) -> bool:
        return schema_version in self.accepted_schema_versions.get(schema_id, ())

    def check_envelope(self, envelope: ObjectEnvelope) -> CheckResult:
        if not self.accepts(envelope.schema_id, envelope.schema_version):
            return fail_result("SchemaOK", FailureCode.UNSUPPORTED_SCHEMA_VERSION)
        return pass_result("SchemaOK")


@dataclass(frozen=True)
class SupportResolution:
    envelope: ObjectEnvelope | None
    pointer_target: Any | None
    reference_edge: ReferenceEdge | None
    status_view: StatusView | None
    digest_check: CheckResult
    migration_check: CheckResult
    redaction_check: CheckResult
    residual_gate_check: CheckResult
    check_result: CheckResult

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer == "":
        return document
    if not pointer.startswith("/"):
        raise VEKError(
            ErrorCode.UNRESOLVED_REFERENCE,
            "JSON Pointer must be empty or begin with '/'",
            details={"pointer": pointer},
        )
    current = document
    for raw_part in pointer.split("/")[1:]:
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if part not in current:
                raise VEKError(
                    ErrorCode.UNRESOLVED_REFERENCE,
                    "JSON Pointer member is missing",
                    details={"pointer": pointer, "member": part},
                )
            current = current[part]
            continue
        if isinstance(current, list):
            if part == "-" or part.startswith("-") or (len(part) > 1 and part.startswith("0")):
                raise VEKError(
                    ErrorCode.UNRESOLVED_REFERENCE,
                    "JSON Pointer array index must be a non-negative integer without leading zeros",
                    details={"pointer": pointer, "index": part},
                )
            try:
                index = int(part)
            except ValueError as exc:
                raise VEKError(
                    ErrorCode.UNRESOLVED_REFERENCE,
                    "JSON Pointer array index is not an integer",
                    details={"pointer": pointer, "index": part},
                ) from exc
            try:
                current = current[index]
            except IndexError as exc:
                raise VEKError(
                    ErrorCode.UNRESOLVED_REFERENCE,
                    "JSON Pointer array index is out of range",
                    details={"pointer": pointer, "index": part},
                ) from exc
            continue
        raise VEKError(
            ErrorCode.UNRESOLVED_REFERENCE,
            "JSON Pointer cannot descend into scalar value",
            details={"pointer": pointer, "part": part},
        )
    return current


class ReferenceResolver:
    def __init__(self, *, bundle_id: str, envelopes: list[ObjectEnvelope]):
        self.bundle_id = bundle_id
        self.envelopes = {envelope.object_id: envelope for envelope in envelopes}

    def resolve(self, ref: ObjectRef) -> tuple[ObjectEnvelope | None, Any | None, CheckResult]:
        if ref.bundle_id != self.bundle_id:
            return None, None, fail_result("RefGraphOK", FailureCode.UNRESOLVED_REFERENCE)
        envelope = self.envelopes.get(ref.object_id)
        if envelope is None:
            return None, None, fail_result("RefGraphOK", FailureCode.UNRESOLVED_REFERENCE)
        if envelope.schema_id != ref.schema_id:
            return envelope, None, fail_result("RefGraphOK", FailureCode.UNSUPPORTED_SCHEMA_VERSION)
        if (
            ref.digest
            and envelope.canonical_digest.value
            and ref.digest.value != envelope.canonical_digest.value
        ):
            return envelope, None, fail_result("RefGraphOK", FailureCode.DIGEST_MISMATCH)
        try:
            target = resolve_pointer(envelope.to_dict(), ref.pointer)
        except VEKError:
            return envelope, None, fail_result("RefGraphOK", FailureCode.UNRESOLVED_REFERENCE)
        return envelope, target, pass_result("RefGraphOK")


class SupportReferenceResolver:
    def __init__(
        self,
        *,
        bundle_id: str,
        envelopes: list[ObjectEnvelope],
        schema_catalogue: SchemaCatalogue,
    ):
        self.raw = ReferenceResolver(bundle_id=bundle_id, envelopes=envelopes)
        self.bundle_id = bundle_id
        self.schema_catalogue = schema_catalogue

    def resolve_support(
        self,
        ref: ObjectRef,
        *,
        require_object: bool = False,
        check_name: str = "SupportRefOK",
    ) -> SupportResolution:
        envelope, target, raw_result = self.raw.resolve(ref)
        edge = (
            ReferenceEdge(
                reference_id=f"{ref.bundle_id}:{ref.object_id}:{ref.pointer}",
                from_object_ref=ref,
                pointer=ref.pointer,
                target_schema=ref.schema_id,
                target_id=ref.object_id,
                target_digest=ref.digest,
                intended_use=ref.intended_use,
            )
            if envelope is not None
            else None
        )
        if not raw_result.passed or envelope is None:
            return self._resolution(
                envelope,
                target,
                edge,
                None,
                raw_result,
                pass_result("MigrationOK"),
                pass_result("RedactionOK"),
                pass_result("ResidualGateOK"),
                fail_result(check_name, *raw_result.failure_codes),
            )
        if require_object and not isinstance(target, dict):
            return self._resolution(
                envelope,
                target,
                edge,
                None,
                raw_result,
                pass_result("MigrationOK"),
                pass_result("RedactionOK"),
                pass_result("ResidualGateOK"),
                fail_result(check_name, FailureCode.UNRESOLVED_REFERENCE),
            )
        status_view, status_result = self._status_view(envelope)
        if not status_result.passed:
            return self._resolution(
                envelope,
                target,
                edge,
                status_view,
                raw_result,
                pass_result("MigrationOK"),
                pass_result("RedactionOK"),
                pass_result("ResidualGateOK"),
                fail_result(check_name, *status_result.failure_codes),
            )
        if status_view.status in {
            LifecycleStatus.STALE,
            LifecycleStatus.REVOKED,
            LifecycleStatus.UNKNOWN,
        }:
            return self._resolution(
                envelope,
                target,
                edge,
                status_view,
                raw_result,
                pass_result("MigrationOK"),
                pass_result("RedactionOK"),
                pass_result("ResidualGateOK"),
                fail_result(check_name, FailureCode.STATUS_BLOCKS_SUPPORT),
            )
        migration = self._migration_check(envelope, status_view)
        redaction = self._redaction_check(envelope)
        residual_gate = self._residual_gate_check(envelope)
        failures = migration.failure_codes + redaction.failure_codes + residual_gate.failure_codes
        result = (
            fail_result(check_name, *failures)
            if failures
            else pass_result(check_name, evidence_refs=(ref.object_id,))
        )
        return self._resolution(
            envelope,
            target,
            edge,
            status_view,
            raw_result,
            migration,
            redaction,
            residual_gate,
            result,
        )

    def _status_view(self, envelope: ObjectEnvelope) -> tuple[StatusView, CheckResult]:
        folded = _status_fold_from_payload(envelope.object_id, envelope.payload)
        if folded is not None:
            return folded
        status = _status_from_payload(envelope.payload)
        if envelope.status_ref is not None:
            _, target, result = self.raw.resolve(envelope.status_ref)
            if not result.passed:
                return (
                    StatusView(envelope.object_id, LifecycleStatus.UNKNOWN),
                    fail_result("StatusOK", FailureCode.UNRESOLVED_REFERENCE),
                )
            folded = _status_fold_from_payload(envelope.object_id, target)
            if folded is not None:
                return folded
            status = _status_from_payload(target)
        if status is None:
            return (
                StatusView(envelope.object_id, LifecycleStatus.UNKNOWN),
                residual_result(
                    "StatusOK",
                    FailureCode.STATUS_BLOCKS_SUPPORT,
                    suggested_repair_hooks=("attach_status_ref_or_lifecycle_status",),
                ),
            )
        return StatusView(envelope.object_id, status), pass_result("StatusOK")

    def _migration_check(self, envelope: ObjectEnvelope, status_view: StatusView) -> CheckResult:
        if status_view.status != LifecycleStatus.MIGRATED:
            return pass_result("MigrationOK")
        payload = envelope.payload
        witness = payload.get("migration_witness_ref") or payload.get("migration_witness")
        catalogue_witness = any(
            key[0] == envelope.schema_id and key[1] == envelope.schema_version
            for key in self.schema_catalogue.migration_witnesses
        )
        if witness or catalogue_witness:
            return pass_result("MigrationOK")
        return fail_result("MigrationOK", FailureCode.STATUS_BLOCKS_SUPPORT)

    def _redaction_check(self, envelope: ObjectEnvelope) -> CheckResult:
        redacted = bool(envelope.payload.get("redacted")) or (
            _status_from_payload(envelope.payload) == LifecycleStatus.REVOKED
            and bool(envelope.payload.get("redaction"))
        )
        if not redacted:
            return pass_result("RedactionOK")
        if envelope.residual_refs or envelope.payload.get("redaction_residual_refs"):
            return pass_result("RedactionOK")
        return fail_result("RedactionOK", FailureCode.STATUS_BLOCKS_SUPPORT)

    def _residual_gate_check(self, envelope: ObjectEnvelope) -> CheckResult:
        gates = envelope.payload.get("residual_gates", ())
        if isinstance(gates, list | tuple) and gates:
            return fail_result(
                "ResidualGateOK",
                FailureCode.AUTHORITY_MISMATCH,
                residual_refs=tuple(str(item) for item in gates),
            )
        return pass_result("ResidualGateOK")

    def _resolution(
        self,
        envelope: ObjectEnvelope | None,
        target: Any | None,
        edge: ReferenceEdge | None,
        status_view: StatusView | None,
        digest_check: CheckResult,
        migration_check: CheckResult,
        redaction_check: CheckResult,
        residual_gate_check: CheckResult,
        result: CheckResult,
    ) -> SupportResolution:
        return SupportResolution(
            envelope=envelope,
            pointer_target=target,
            reference_edge=edge,
            status_view=status_view,
            digest_check=digest_check,
            migration_check=migration_check,
            redaction_check=redaction_check,
            residual_gate_check=residual_gate_check,
            check_result=result,
        )


def _status_from_payload(value: object) -> LifecycleStatus | None:
    if not isinstance(value, dict):
        return None
    for key in ("lifecycle_status", "status", "decision_status", "post_status"):
        if key in value:
            try:
                return LifecycleStatus(str(value[key]))
            except ValueError:
                return LifecycleStatus.UNKNOWN
    payload = value.get("payload")
    if isinstance(payload, dict):
        return _status_from_payload(payload)
    return None


def _status_fold_from_payload(
    object_id: str, value: object
) -> tuple[StatusView, CheckResult] | None:
    if not isinstance(value, dict):
        return None
    raw_events = value.get("status_events")
    if not isinstance(raw_events, list):
        return None
    events: list[StatusEvent] = []
    for raw in raw_events:
        if not isinstance(raw, dict):
            return None
        try:
            events.append(
                StatusEvent(
                    object_id=str(raw.get("object_id", object_id)),
                    pre_status=LifecycleStatus(str(raw.get("pre_status", "unknown"))),
                    post_status=LifecycleStatus(str(raw.get("post_status", "unknown"))),
                    cause=str(raw.get("cause", "status fold")),
                    actor_authority_ref=str(raw.get("actor_authority_ref", "local")),
                    ledger_event_ref=str(raw.get("ledger_event_ref", "")),
                    invalidation_trigger=str(raw.get("invalidation_trigger", "")),
                    migration_target=str(raw.get("migration_target", "")),
                    residual_disposition=tuple(
                        str(item) for item in raw.get("residual_disposition", ())
                    ),
                    predecessor_event_ref=raw.get("predecessor_event_ref"),
                    provenance=tuple(str(item) for item in raw.get("provenance", ())),
                    status_event_id=str(raw.get("status_event_id") or raw.get("id") or ""),
                )
            )
        except ValueError:
            return StatusFold().fold(object_id, [])
    return StatusFold().fold(object_id, events)
