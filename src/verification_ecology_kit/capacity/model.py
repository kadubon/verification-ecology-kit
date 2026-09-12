"""Closed finite contract records, distinct from established VET-Core encodings."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from fractions import Fraction
from importlib.resources import files
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker

from verification_ecology_kit.digest import DigestPolicy


def digest(value: Any) -> str:
    return DigestPolicy().digest_json(value).value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def natural(value: int, maximum: int = 1_000_000) -> None:
    require(type(value) is int and 0 <= value <= maximum, "bounded integer required")


@dataclass(frozen=True)
class Resource:
    resource_id: str
    unit: str
    kind: str
    capacity: tuple[int, ...]


@dataclass(frozen=True)
class Service:
    service_id: str
    version: str
    domain: str
    checks: tuple[str, ...]
    interface: str
    valid_until: int
    exposures: tuple[str, ...]
    dependence_known: bool
    support_refs: tuple[str, ...]
    assumptions: tuple[str, ...]
    evidence_basis: str


@dataclass(frozen=True)
class Work:
    work_id: str
    residual_id: str
    subject_digest: str
    input_digest: str
    rule_version: str
    check: str
    domain: str
    bundle: str
    arrival: int
    deadline: int
    protected: bool
    required: bool
    predecessors: tuple[str, ...]
    separate_from: tuple[str, ...]


@dataclass(frozen=True)
class Action:
    action_id: str
    work_id: str
    service_id: str
    kind: str
    duration: int
    costs: tuple[int, ...]
    requires_success: tuple[str, ...]
    requires_negative: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    outcomes: tuple[str, ...]
    assumption: str


@dataclass(frozen=True)
class Contract:
    contract_id: str
    scope: str
    time_origin: str
    slot_seconds: str
    horizon: int
    max_candidates: int
    max_events: int
    resources: tuple[Resource, ...]
    services: tuple[Service, ...]
    work: tuple[Work, ...]
    actions: tuple[Action, ...]
    scenarios: tuple[Scenario, ...]
    schema_version: str = "vek.capacity.contract.v1"
    semantics: str = "nonpreemptive-integer-slots"
    work_unit: str = "registered-check"
    observation_policy: str = "replan-after-admitted-result"

    def __post_init__(self) -> None:
        validate_schema("capacity-contract", self.to_dict())
        duration = Fraction(self.slot_seconds)
        require(duration > 0 and duration.numerator <= 1_000_000, "invalid slot duration")
        require(duration.denominator <= 1_000_000, "slot denominator too large")
        for group, key in (
            (self.resources, "resource_id"),
            (self.services, "service_id"),
            (self.work, "work_id"),
            (self.actions, "action_id"),
            (self.scenarios, "scenario_id"),
        ):
            require(len({getattr(x, key) for x in group}) == len(group), "duplicate identity")
        works = {w.work_id: w for w in self.work}
        services = {s.service_id: s for s in self.services}
        actions = {a.action_id: a for a in self.actions}
        identities = [
            (w.residual_id, w.subject_digest, w.input_digest, w.rule_version, w.check)
            for w in self.work
        ]
        require(len(set(identities)) == len(identities), "duplicate registered check")
        for r in self.resources:
            require(
                len(r.capacity) == (self.horizon if r.kind == "pool" else 1),
                "resource horizon mismatch",
            )
        for w in self.work:
            require(not w.protected or w.required, "protected work must be required")
            require(
                w.arrival < self.horizon and w.arrival < w.deadline <= self.horizon,
                "work time outside horizon",
            )
            require(set(w.predecessors + w.separate_from) <= works.keys(), "unknown work relation")
            require(w.work_id not in w.predecessors + w.separate_from, "self dependence")
            require(
                all(works[x].domain == w.domain for x in w.separate_from),
                "separation requires same registered domain",
            )
        for a in self.actions:
            require(a.work_id in works and a.service_id in services, "unknown action target")
            require(len(a.costs) == len(self.resources), "resource coordinates mismatch")
            require(
                set(a.requires_success + a.requires_negative) <= actions.keys(),
                "unknown activation prerequisite",
            )
            s, w = services[a.service_id], works[a.work_id]
            require(s.domain == w.domain and w.check in s.checks, "ineligible service domain/check")
            require(a.duration <= self.horizon, "duration outside horizon")
        for scenario in self.scenarios:
            require(len(scenario.outcomes) == len(self.actions), "joint outcome vector mismatch")
        # The finite relation must be acyclic, even for currently unselected actions.
        edges = {
            a.action_id: set(a.requires_success + a.requires_negative)
            | {b.action_id for b in self.actions if b.work_id in works[a.work_id].predecessors}
            for a in self.actions
        }
        for _ in self.actions:
            ready = {key for key, deps in edges.items() if not deps}
            edges = {key: deps - ready for key, deps in edges.items() if key not in ready}
        require(not edges, "cyclic dependencies")

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(asdict(self)))

    @property
    def contract_digest(self) -> str:
        return digest(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Contract:
        validate_schema("capacity-contract", data)
        values = dict(data)
        for key, kind, tuples in (
            ("resources", Resource, ("capacity",)),
            ("services", Service, ("checks", "exposures", "support_refs", "assumptions")),
            ("work", Work, ("predecessors", "separate_from")),
            ("actions", Action, ("costs", "requires_success", "requires_negative")),
            ("scenarios", Scenario, ("outcomes",)),
        ):
            values[key] = tuple(
                kind(**cast(Any, {k: tuple(v) if k in tuples else v for k, v in item.items()}))
                for item in data[key]
            )
        return cls(**values)


def validate_schema(name: str, value: Any) -> None:
    def exact_numbers(item: Any) -> None:
        require(not isinstance(item, float), "floating-point quantities are unsupported")
        if isinstance(item, dict):
            for child in item.values():
                exact_numbers(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                exact_numbers(child)

    exact_numbers(value)
    schema = json.loads(
        files("verification_ecology_kit")
        .joinpath("schemas", f"{name}.schema.json")
        .read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
