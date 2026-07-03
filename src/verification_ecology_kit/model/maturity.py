"""Maturity profile audit view."""

from __future__ import annotations

from dataclasses import dataclass

from verification_ecology_kit.model.records import jsonable


@dataclass
class MaturityProfile:
    lineage_coverage: tuple[str, ...] = ()
    residual_liveness: tuple[str, ...] = ()
    boundary_control: tuple[str, ...] = ()
    aperture_accounting: tuple[str, ...] = ()
    federation_readiness: tuple[str, ...] = ()
    schema_revision_capacity: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    unresolved_residual_count: int = 0
    stale_certificate_count: int = 0
    unknown_certificate_count: int = 0
    checker_status_residual_count: int = 0
    open_counterexample_channels: tuple[str, ...] = ()
    scalar_dashboard_label: str = ""
    evidence_not_replaced_by_label: bool = True

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
