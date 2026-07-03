"""Boundary records for destructive and narrowing exposure."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.model.records import jsonable
from verification_ecology_kit.result import CheckResult, FailureCode, pass_result, residual_result


@dataclass
class BoundaryRecord:
    boundary_id: str
    predicate: str
    destructive_predicate: str = ""
    narrowing_predicate: str = ""
    irreversible_modes: tuple[str, ...] = ()
    boundary_assumptions: tuple[str, ...] = ()
    aperture_loss_modes: tuple[str, ...] = ()
    translation_loss_modes: tuple[str, ...] = ()
    residual_loss_modes: tuple[str, ...] = ()
    question_form_loss_modes: tuple[str, ...] = ()
    reachability_certificate_refs: tuple[str, ...] = ()
    unexcluded_residuals: tuple[str, ...] = ()
    invalidation_conditions: tuple[str, ...] = ()
    recheck_trigger: str = ""
    provenance: tuple[str, ...] = ()

    def check(self) -> CheckResult:
        if self.unexcluded_residuals:
            return residual_result(
                "BoundarySafety",
                FailureCode.BOUNDARY_UNCHECKED,
                residual_refs=self.unexcluded_residuals,
            )
        if not self.reachability_certificate_refs:
            return residual_result(
                "BoundarySafety",
                FailureCode.BOUNDARY_UNCHECKED,
                suggested_repair_hooks=("attach_reachability_certificate",),
            )
        return pass_result("BoundarySafety", evidence_refs=self.reachability_certificate_refs)

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
