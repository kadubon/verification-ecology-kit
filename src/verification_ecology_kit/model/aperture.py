"""Aperture capacity profiles and comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from verification_ecology_kit.model.records import jsonable


class ApertureComparison(StrEnum):
    PRESERVED = "preserved"
    ENLARGED = "enlarged"
    NARROWED_WITH_LIVE_RESIDUAL = "narrowed_with_live_residual"
    NARROWED_WITH_INERT_RESIDUAL = "narrowed_with_inert_residual"
    NARROWED_WITH_RESIDUAL = "narrowed_with_live_residual"
    NARROWED_WITHOUT_RESIDUAL = "narrowed_without_residual"
    INCOMPARABLE = "incomparable"


@dataclass(frozen=True)
class CapacityRecord:
    name: str
    represented_capability: tuple[str, ...] = ()
    nominal_capacity: int = 0
    feasible_capacity: int = 0
    exercised_capacity: int = 0
    resource_bounds: tuple[str, ...] = ()
    cost_bounds: tuple[str, ...] = ()
    latency_bounds: tuple[str, ...] = ()
    residual_obligations: tuple[str, ...] = ()
    inert_residual_obligations: tuple[str, ...] = ()

    def has_debt(self) -> bool:
        return (
            self.nominal_capacity > self.feasible_capacity
            or bool(self.residual_obligations)
            or bool(self.inert_residual_obligations)
        )


@dataclass
class Aperture:
    question_form_capacity: CapacityRecord = field(
        default_factory=lambda: CapacityRecord("question_form")
    )
    residual_type_capacity: CapacityRecord = field(
        default_factory=lambda: CapacityRecord("residual_type")
    )
    translation_channel_capacity: CapacityRecord = field(
        default_factory=lambda: CapacityRecord("translation_channel")
    )
    counter_packet_capacity: CapacityRecord = field(
        default_factory=lambda: CapacityRecord("counter_packet")
    )
    schema_revision_capacity: CapacityRecord = field(
        default_factory=lambda: CapacityRecord("schema_revision")
    )
    self_verification_capacity: CapacityRecord = field(
        default_factory=lambda: CapacityRecord("self_verification")
    )

    def components(self) -> tuple[CapacityRecord, ...]:
        return (
            self.question_form_capacity,
            self.residual_type_capacity,
            self.translation_channel_capacity,
            self.counter_packet_capacity,
            self.schema_revision_capacity,
            self.self_verification_capacity,
        )

    def strict_capacity_leq(self, other: Aperture) -> bool:
        return all(
            before.feasible_capacity <= after.feasible_capacity
            for before, after in zip(self.components(), other.components(), strict=True)
        )

    def accountable_loss_leq(self, other: Aperture) -> bool:
        for before, after in zip(self.components(), other.components(), strict=True):
            if (
                before.feasible_capacity > after.feasible_capacity
                and not after.residual_obligations
                and not after.inert_residual_obligations
            ):
                return False
        return True

    def loss_has_live_residuals(self, other: Aperture) -> bool:
        for before, after in zip(self.components(), other.components(), strict=True):
            if before.feasible_capacity > after.feasible_capacity and after.residual_obligations:
                return True
        return False

    def loss_has_only_inert_residuals(self, other: Aperture) -> bool:
        loss_seen = False
        for before, after in zip(self.components(), other.components(), strict=True):
            if before.feasible_capacity <= after.feasible_capacity:
                continue
            loss_seen = True
            if after.residual_obligations:
                return False
            if not after.inert_residual_obligations:
                return False
        return loss_seen

    def compare(self, other: Aperture) -> ApertureComparison:
        before = self.components()
        after = other.components()
        if len(before) != len(after):
            return ApertureComparison.INCOMPARABLE
        strict = self.strict_capacity_leq(other)
        reverse = other.strict_capacity_leq(self)
        if strict and not reverse:
            return ApertureComparison.ENLARGED
        if strict and reverse:
            return ApertureComparison.PRESERVED
        if self.loss_has_live_residuals(other):
            return ApertureComparison.NARROWED_WITH_LIVE_RESIDUAL
        if self.loss_has_only_inert_residuals(other):
            return ApertureComparison.NARROWED_WITH_INERT_RESIDUAL
        if self.accountable_loss_leq(other):
            return ApertureComparison.NARROWED_WITH_LIVE_RESIDUAL
        return ApertureComparison.NARROWED_WITHOUT_RESIDUAL

    def aperture_debts(self) -> tuple[str, ...]:
        return tuple(component.name for component in self.components() if component.has_debt())

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
