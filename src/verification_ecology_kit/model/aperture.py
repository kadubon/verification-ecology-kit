"""Aperture capacity profiles and comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from verification_ecology_kit.model.records import jsonable


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

    def has_debt(self) -> bool:
        return self.nominal_capacity > self.feasible_capacity or bool(self.residual_obligations)


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
            ):
                return False
        return True

    def aperture_debts(self) -> tuple[str, ...]:
        return tuple(component.name for component in self.components() if component.has_debt())

    def to_dict(self) -> dict[str, object]:
        return jsonable(self)
