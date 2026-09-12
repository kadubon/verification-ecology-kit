"""Independent schedule expansion; never imports or calls the selector."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from fractions import Fraction
from typing import Any

from verification_ecology_kit.capacity.model import (
    Contract,
    digest,
    natural,
    require,
    validate_schema,
)


@dataclass
class Snapshot:
    revision: int = 0
    clock: int = 0
    completed: dict[str, str] = field(default_factory=dict)
    reservations: dict[str, int] = field(default_factory=dict)
    dispatched: set[str] = field(default_factory=set)
    spent: list[int] = field(default_factory=list)
    withdrawn: set[str] = field(default_factory=set)
    cancelled: set[str] = field(default_factory=set)
    attempts: dict[str, int] = field(default_factory=dict)
    repair: set[str] = field(default_factory=set)
    results: dict[str, str] = field(default_factory=dict)
    completed_actions: dict[str, str] = field(default_factory=dict)
    completion_times: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            key: sorted(value) if isinstance(value, set) else value
            for key, value in asdict(self).items()
        }

    @property
    def source_digest(self) -> str:
        return digest(self.to_dict())


@dataclass(frozen=True)
class Checked:
    objective: tuple[Fraction, ...]
    branches: tuple[dict[str, Any], ...]
    mandatory_met: bool
    reservations: tuple[tuple[int, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": [str(x) for x in self.objective],
            "branches": list(self.branches),
            "mandatory_met": self.mandatory_met,
            "reservations": [list(x) for x in self.reservations],
        }


def check_schedule(c: Contract, s: Snapshot, schedule: dict[str, int]) -> Checked:
    """Reconstruct occupancy and all declared joint branches from submitted assignments.

    All slots are reserved nonadaptively. A failed success-prerequisite stops dependent
    work; its reservation remains conservatively held until explicit cancellation.
    """
    require(len(schedule) <= len(c.actions), "schedule bound exceeded")
    require(len(s.spent) == len(c.resources), "invalid resource snapshot")
    actions = {a.action_id: a for a in c.actions}
    works = {w.work_id: w for w in c.work}
    services = {v.service_id: v for v in c.services}
    require(set(schedule) <= actions.keys(), "unknown scheduled action")
    require(not set(schedule) & s.reservations.keys(), "action already reserved")
    merged = s.reservations | schedule
    require(len({actions[x].work_id for x in merged}) == len(merged), "duplicate work service")
    occupancy = [[0] * c.horizon for _ in c.resources]
    budgets = list(s.spent)
    for aid, start in merged.items():
        natural(start, c.horizon)
        a = actions[aid]
        w, v = works[a.work_id], services[a.service_id]
        end = start + a.duration
        if aid in schedule:
            require(start >= max(s.clock, w.arrival), "work before arrival/current clock")
            require(
                w.work_id not in s.completed and w.work_id not in s.cancelled,
                "work is no longer pending",
            )
            require(v.service_id not in s.withdrawn, "withdrawn service")
            require(end <= v.valid_until, "expired domain evidence; revalidation required")
        require(end <= c.horizon, "work outside horizon")
        for i, r in enumerate(c.resources):
            if r.kind == "pool":
                held_until = c.horizon if aid in s.dispatched and end <= s.clock else end
                for slot in range(start, held_until):
                    occupancy[i][slot] += a.costs[i]
            else:
                budgets[i] += a.costs[i]
    for i, r in enumerate(c.resources):
        if r.kind == "pool":
            require(
                all(occupancy[i][t] <= r.capacity[t] for t in range(s.clock, c.horizon)),
                f"shared pool exceeded: {r.resource_id}",
            )
        else:
            require(budgets[i] <= r.capacity[0], f"consumable budget exceeded: {r.resource_id}")
    selected_work = {actions[aid].work_id: aid for aid in merged}
    for aid, start in merged.items():
        a, w = actions[aid], works[actions[aid].work_id]
        for predecessor in w.predecessors:
            require(
                predecessor in s.completed
                or (
                    predecessor in selected_work
                    and merged[selected_work[predecessor]]
                    + actions[selected_work[predecessor]].duration
                    <= start
                ),
                "missing/late predecessor",
            )
        for prerequisite in a.requires_success + a.requires_negative:
            if prerequisite in merged:
                require(
                    merged[prerequisite] + actions[prerequisite].duration <= start,
                    "activation retry completes after dependent start",
                )
            require(
                s.completed_actions.get(prerequisite)
                == ("negative" if prerequisite in a.requires_negative else "positive")
                or (aid in s.reservations and prerequisite in s.completed_actions)
                or (
                    prerequisite in merged
                    and merged[prerequisite] + actions[prerequisite].duration <= start
                ),
                "missing/late activation prerequisite",
            )
        for other in w.separate_from:
            other_aid = selected_work.get(other)
            if other in s.completed:
                other_aid = next(
                    (x for x in s.completed_actions if actions[x].work_id == other), None
                )
            if other_aid is not None:
                left, right = services[a.service_id], services[actions[other_aid].service_id]
                require(
                    left.dependence_known
                    and right.dependence_known
                    and bool(left.exposures)
                    and bool(right.exposures)
                    and not set(left.exposures) & set(right.exposures),
                    "uncertified separation",
                )
    branches: list[dict[str, Any]] = []
    scores: list[tuple[Fraction, ...]] = []
    domains = sorted({w.domain for w in c.work if w.required})
    bundles = {(w.domain, w.bundle) for w in c.work if w.required}
    require(bool(domains), "no required check bundles")
    required = {w.work_id for w in c.work if w.protected}
    for scenario in c.scenarios:
        completed = dict(s.completed)
        outcomes = dict(s.completed_actions)
        ends = {wid: s.completion_times.get(wid, s.clock) for wid in completed}
        costs = list(s.spent)
        repair = set(s.repair)
        for aid in sorted(merged, key=lambda key: (merged[key], key)):
            a = actions[aid]
            w = works[a.work_id]
            if aid in s.reservations and merged[aid] + a.duration <= s.clock:
                continue  # Unknown completion cannot become an observation by passage of time.
            if not all(outcomes.get(p) == "positive" for p in a.requires_success):
                continue
            if not all(outcomes.get(p) == "negative" for p in a.requires_negative):
                continue
            if not all(p in completed for p in w.predecessors):
                continue
            outcome = scenario.outcomes[
                next(i for i, x in enumerate(c.actions) if x.action_id == aid)
            ]
            outcomes[aid] = outcome
            for i, r in enumerate(c.resources):
                costs[i] += a.costs[i] * (a.duration if r.kind == "pool" else 1)
            if outcome in {"positive", "negative"}:
                completed[w.work_id] = outcome
                ends[w.work_id] = merged[aid] + a.duration
                if outcome == "negative":
                    repair.add(w.work_id)
                if a.kind == "repair" and outcome == "positive":
                    repair -= {actions[x].work_id for x in a.requires_negative}
        done_bundles = {
            (domain, bundle)
            for domain, bundle in bundles
            if all(
                w.work_id in completed for w in c.work if (w.domain, w.bundle) == (domain, bundle)
            )
        }
        coverage = min(
            Fraction(
                sum(d == domain for d, _ in done_bundles), sum(d == domain for d, _ in bundles)
            )
            for domain in domains
        )
        protected_done = sum(
            wid in completed and ends[wid] <= works[wid].deadline for wid in required
        )
        due_missed = sorted(
            w.work_id for w in c.work if w.work_id not in completed or ends[w.work_id] > w.deadline
        )
        age_credit = sum(c.horizon - works[wid].arrival for wid in completed if works[wid].required)
        score = (
            Fraction(protected_done),
            coverage,
            Fraction(age_credit),
            Fraction(-sum(works[x].required for x in due_missed)),
            *(Fraction(-x) for x in costs),
        )
        # Verdict sign is deliberately absent from ranking. Repair is visible, not a
        # penalty against sound negative checking of the same required obligation.
        scores.append(score)
        trace = []
        for t in range(c.horizon + 1):
            arrived = sum(w.arrival <= t for w in c.work)
            done = sum(ends.get(w.work_id, c.horizon + 1) <= t for w in c.work)
            trace.append(arrived - done - sum(works[x].arrival <= t for x in s.cancelled))
        branches.append(
            {
                "scenario": scenario.scenario_id,
                "completed": sorted(completed),
                "completed_bundles": [list(x) for x in sorted(done_bundles)],
                "missed_deadlines": due_missed,
                "repair": sorted(repair),
                "costs": costs,
                "backlog": trace,
                "backlog_peak": max(trace),
                "unfinished": len(c.work) - len(completed) - len(s.cancelled),
                "mandatory_met": protected_done == len(required),
            }
        )
    return Checked(
        tuple(min(score[i] for score in scores) for i in range(len(scores[0]))),
        tuple(branches),
        all(b["mandatory_met"] for b in branches),
        tuple(tuple(row) for row in occupancy),
    )


def check_plan(c: Contract, s: Snapshot, plan: dict[str, Any]) -> Checked:
    validate_schema("capacity-plan", plan)
    require(
        set(plan)
        == {"contract_digest", "source_digest", "revision", "schedule", "checked", "search"},
        "invalid plan fields",
    )
    require(
        plan["contract_digest"] == c.contract_digest
        and plan["source_digest"] == s.source_digest
        and plan["revision"] == s.revision,
        "stale or substituted plan",
    )
    checked = check_schedule(c, s, plan["schedule"])
    require(checked.to_dict() == plan["checked"], "tampered objective/witness")
    return checked
