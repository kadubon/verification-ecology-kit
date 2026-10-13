"""Generate closed schemas for the experimental finite capacity profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / "src/verification_ecology_kit/schemas"
TEXT = {"type": "string", "minLength": 1, "maxLength": 256}
NAT = {"type": "integer", "minimum": 0, "maximum": 1_000_000}
BOOL = {"type": "boolean"}
DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}


def array(item: dict[str, Any], limit: int = 32, minimum: int = 0) -> dict[str, Any]:
    return {"type": "array", "items": item, "minItems": minimum, "maxItems": limit}


def enum(*values: str) -> dict[str, Any]:
    return {"enum": list(values)}


def obj(**properties: Any) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def main() -> None:
    service = obj(
        service_id=TEXT,
        version=TEXT,
        domain=TEXT,
        checks=array(TEXT, minimum=1),
        interface=TEXT,
        valid_until=NAT,
        exposures=array(TEXT),
        dependence_known=BOOL,
        support_refs=array(TEXT, minimum=1),
        assumptions=array(TEXT, minimum=1),
        evidence_basis=enum("synthetic", "declared-model", "observed-record"),
    )
    work = obj(
        work_id=TEXT,
        residual_id=TEXT,
        subject_digest=DIGEST,
        input_digest=DIGEST,
        rule_version=TEXT,
        check=TEXT,
        domain=TEXT,
        bundle=TEXT,
        arrival=NAT,
        deadline=NAT,
        protected=BOOL,
        required=BOOL,
        predecessors=array(TEXT),
        separate_from=array(TEXT),
    )
    action = obj(
        action_id=TEXT,
        work_id=TEXT,
        service_id=TEXT,
        kind=enum("check", "repair", "construct", "calibrate", "counter-check", "activate"),
        duration={"type": "integer", "minimum": 1, "maximum": 16},
        costs=array(NAT, 8, 1),
        requires_success=array(TEXT),
        requires_negative=array(TEXT),
    )
    outcome = enum("positive", "negative", "inconclusive", "invalid", "timeout")
    contract = obj(
        contract_id=TEXT,
        scope=TEXT,
        time_origin=TEXT | {"format": "date-time"},
        slot_seconds={"type": "string", "pattern": "^[1-9][0-9]{0,6}(/[1-9][0-9]{0,6})?$"},
        horizon={"type": "integer", "minimum": 1, "maximum": 16},
        max_candidates={"type": "integer", "minimum": 1, "maximum": 100000},
        max_events={"type": "integer", "minimum": 1, "maximum": 1024},
        resources=array(
            obj(
                resource_id=TEXT, unit=TEXT, kind=enum("pool", "budget"), capacity=array(NAT, 16, 1)
            ),
            8,
            1,
        ),
        services=array(service, 16, 1),
        work=array(work, 12, 1),
        actions=array(action, 12, 1),
        scenarios=array(
            obj(scenario_id=TEXT, outcomes=array(outcome, 12, 1), assumption=TEXT), 8, 1
        ),
        schema_version={"const": "vek.capacity.contract.v1"},
        semantics={"const": "nonpreemptive-integer-slots"},
        work_unit={"const": "registered-check"},
        observation_policy={"const": "replan-after-admitted-result"},
    )
    rational = {"type": "string", "pattern": "^-?[0-9]+(/[1-9][0-9]*)?$", "maxLength": 64}
    branch = obj(
        scenario=TEXT,
        completed=array(TEXT),
        completed_bundles=array(array(TEXT, 2, 2)),
        missed_deadlines=array(TEXT),
        repair=array(TEXT),
        costs=array(NAT, 8, 1),
        backlog=array(NAT, 17, 1),
        backlog_peak=NAT,
        unfinished=NAT,
        mandatory_met=BOOL,
    )
    checked = obj(
        objective=array(rational, 12, 1),
        branches=array(branch, 8, 1),
        mandatory_met=BOOL,
        reservations=array(array(NAT, 16, 1), 8, 1),
        unallocated_followups=array(TEXT, 12),
    )
    search = obj(
        complete=BOOL,
        candidates=NAT | {"maximum": 17**12},
        examined=NAT,
        valid=NAT,
        budget=NAT,
        checker_calls=NAT,
        rejections={"type": "object", "maxProperties": 64, "additionalProperties": NAT},
        status=enum("feasible", "infeasible", "unknown"),
        optimality=enum("finite-catalogue", "checked-incumbent"),
    )
    plan = obj(
        contract_digest=DIGEST,
        source_digest=DIGEST,
        revision=NAT,
        schedule={"type": "object", "maxProperties": 12, "additionalProperties": NAT},
        checked=checked,
        search=search,
    )
    report = obj(
        record_type={"const": "vek_verification_capacity_report_v1"},
        schema_version={"const": "1"},
        producer_version=TEXT,
        contract_digest=DIGEST,
        source_digest=DIGEST,
        snapshot_revision=NAT,
        scope=TEXT,
        evidence_basis={"const": "declared-model"},
        time_origin=TEXT,
        slot_seconds=TEXT,
        horizon=NAT,
        work_unit={"const": "registered-check"},
        domains=array(TEXT),
        planning_assumptions=array(TEXT, 512),
        service_guaranteed_lower_envelope={"type": "null"},
        observed_service={"type": "null"},
        local_accounting=obj(
            completed=NAT,
            reserved=NAT,
            attempts=NAT,
            consumed=array(NAT, 8, 1),
            unfinished=NAT,
            repair=array(TEXT),
            elapsed_seconds=rational,
            descriptive_completion_rate={"anyOf": [rational, {"type": "null"}]},
            evidence_basis={"const": "synthetic-or-declared-model"},
        ),
        resources=contract["properties"]["resources"],
        work=array(work, 12, 1),
        unsupported_dependence=array(TEXT),
        pending_followup_work=array(
            obj(
                work_id=TEXT,
                subject_digest=DIGEST,
                source_residual=TEXT,
                rule_version=TEXT,
                arrival=NAT,
                parent_work=TEXT,
            ),
            12,
        ),
        forecast=checked,
        search=search,
        non_claims=array(TEXT),
    )
    result = obj(
        result_id=TEXT,
        action_id=TEXT,
        work_id=TEXT,
        subject_digest=DIGEST,
        input_digest=DIGEST,
        service_id=TEXT,
        service_version=TEXT,
        interface=TEXT,
        attempt=NAT,
        outcome=outcome,
        costs=array(NAT, 8, 1),
        start=NAT,
        end=NAT,
        completed_work={"type": "integer", "minimum": 0, "maximum": 1},
        evidence_basis=enum("synthetic", "declared-model", "observed-record"),
        support_refs=array(TEXT, minimum=1),
        contract_digest=DIGEST,
        scope=TEXT,
    )
    schemas = {
        "capacity-contract": contract,
        "capacity-plan": plan,
        "capacity-report": report,
        "capacity-result": result,
    }
    for name, schema in schemas.items():
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"https://verification-ecology-kit.org/schemas/{name}.schema.json",
            "title": name,
            **schema,
        }
        (ROOT / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
