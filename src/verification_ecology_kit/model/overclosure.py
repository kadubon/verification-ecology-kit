"""Overclosure, schema-overclosure, and monoculture detectors."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.model.records import ResidualKind, jsonable
from verification_ecology_kit.model.residuals import ResidualRecord
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result


@dataclass
class OverclosureWitness:
    witness_id: str
    gain_record: tuple[str, ...]
    scope_and_measurement_context: tuple[str, ...]
    regression_records: tuple[str, ...]
    measurement_assumptions: tuple[str, ...]
    residual_adequacy_record: tuple[str, ...]
    provenance: tuple[str, ...]
    falsification_condition: str = ""
    negative_evidence_channel: str = ""
    repair_or_tightening_hooks: tuple[str, ...] = ()

    def is_overclosing(self) -> bool:
        return bool(
            self.gain_record and self.regression_records and not self.residual_adequacy_record
        )

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)


class SchemaOverclosureDetector:
    def detect(
        self,
        *,
        schema_rejected_unknown: bool,
        suppressed_residuals: tuple[str, ...] = (),
        dashboard_hid_component_failure: bool = False,
        incompatible_residuals_suppressed: tuple[str, ...] = (),
        anti_overclosure_rigid_labels: bool = False,
        field_rename_without_migration_witness: bool = False,
        required_field_added_without_migration_residual: bool = False,
        additional_properties_false_without_escape_hatch: bool = False,
    ) -> tuple[CheckResult, list[ResidualRecord]]:
        residuals: list[ResidualRecord] = []
        if (
            schema_rejected_unknown
            or suppressed_residuals
            or dashboard_hid_component_failure
            or incompatible_residuals_suppressed
            or anti_overclosure_rigid_labels
            or field_rename_without_migration_witness
            or required_field_added_without_migration_residual
            or additional_properties_false_without_escape_hatch
        ):
            residual = ResidualRecord(
                kind=ResidualKind.SCHEMA_OVERCLOSURE,
                origin="schema",
                scope=("schema",),
                obligation=(
                    "Repair schema, fork schema, or preserve local extension for unknown residuals"
                ),
                payload={
                    "suppressed_residuals": list(suppressed_residuals),
                    "dashboard_hid_component_failure": dashboard_hid_component_failure,
                    "incompatible_residuals_suppressed": list(incompatible_residuals_suppressed),
                    "anti_overclosure_rigid_labels": anti_overclosure_rigid_labels,
                    "field_rename_without_migration_witness": (
                        field_rename_without_migration_witness
                    ),
                    "required_field_added_without_migration_residual": (
                        required_field_added_without_migration_residual
                    ),
                    "additional_properties_false_without_escape_hatch": (
                        additional_properties_false_without_escape_hatch
                    ),
                },
                exposure="blocks_support",
            )
            residuals.append(residual)
            return (
                residual_result(
                    "SchemaOverclosure",
                    FailureCode.SCHEMA_OVERCLOSURE,
                    residual_refs=(residual.residual_id,),
                    suggested_repair_hooks=("schema_repair", "schema_fork", "local_extension"),
                ),
                residuals,
            )
        return pass_result("SchemaOverclosure"), residuals


class VerifierMonocultureDetector:
    def detect(
        self,
        *,
        origin_assumptions: list[tuple[str, ...]],
        question_forms: list[tuple[str, ...]],
        residual_filters: list[tuple[str, ...]],
        counter_packet_routes: list[tuple[str, ...]],
    ) -> CheckResult:
        shared_origin = self._all_share(origin_assumptions)
        shared_questions = self._all_share(question_forms)
        shared_filters = self._all_share(residual_filters)
        missing_counter_routes = any(not routes for routes in counter_packet_routes)
        if shared_origin or shared_questions or shared_filters or missing_counter_routes:
            return residual_result(
                "VerifierMonoculture",
                FailureCode.OVERCLOSURE_RISK,
                suggested_repair_hooks=("add_counter_packet_routes", "diversify_question_forms"),
            )
        return pass_result("VerifierMonoculture")

    def _all_share(self, values: list[tuple[str, ...]]) -> bool:
        if len(values) < 2:
            return False
        shared = set(values[0])
        for item in values[1:]:
            shared &= set(item)
        return bool(shared)
