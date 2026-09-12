"""Pinned optional CCR task proposals; CAIT receives the VEK-owned JSON report."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from verification_ecology_kit.capacity.model import Contract, require

CCR_COMMIT = "6d8a30820806044b3a4b18d499fbe89bef83fbf2"
CAIT_COMMIT = "8ef4bc1ea272751804655a6e056467837ff35670"


def ccr_proposals(
    c: Contract, *, revision: str, pool_ids: list[str], schema_version: str = "ccr.task.v0.1"
) -> list[dict[str, Any]]:
    require(schema_version == "ccr.task.v0.1", "unsupported CCR schema mapping")
    require(bool(revision) and len(pool_ids) == len(c.resources), "CCR pool/revision required")
    schema = json.loads(
        files("verification_ecology_kit.capacity")
        .joinpath("fixtures/ccr-task.schema.json")
        .read_text(encoding="utf-8")
    )
    proposals = []
    for w in c.work:
        actions = [a for a in c.actions if a.work_id == w.work_id]
        task = {
            "schema_version": schema_version,
            "task_id": f"vek-{w.work_id}",
            "created_at": c.time_origin,
            "status": "open",
            "role": "verifier",
            "title": f"Verify {w.check}",
            "objective": f"Complete registered check {w.work_id}",
            "inputs": [
                {"ref": w.residual_id, "kind": "residual", "required": True},
                {"ref": w.subject_digest, "kind": "artifact", "required": True},
            ],
            "expected_outputs": [
                {
                    "kind": "verifier_report",
                    "schema_ref": "vek.capacity.result.v1",
                    "destination": "proposed-local-admission",
                }
            ],
            "constraints": {
                "side_effect_policy": "operator_approval_required",
                "network_policy": "none",
                "authority_policy": "read_only",
                "max_runtime_minutes": 1,
            },
            "lease": {"lease_required": True, "ttl_minutes": 1},
            "verifier_plan": {
                "required_verifiers": sorted({a.service_id for a in actions}),
                "promotion_gate": "custom",
                "failure_route": "repair_task",
            },
            "residual_policy": {
                "preserve_residuals": True,
                "blocking_residuals_prevent_settlement": True,
            },
            "pic_interop": {
                "enabled": False,
                "recommended_pic_commands": [],
                "pic_profile": "research",
                "candidate_only_until_checked": True,
            },
            "extensions": {
                "x_vek_capacity": {
                    "proposal_only": True,
                    "contract_digest": c.contract_digest,
                    "domain": w.domain,
                    "input_digest": w.input_digest,
                    "source_residual": w.residual_id,
                    "required_check": w.check,
                    "separate_from": list(w.separate_from),
                    "cost_bounds": [list(a.costs) for a in actions],
                    "expiry_slot": w.deadline,
                    "slot_seconds": c.slot_seconds,
                    "ccr_revision": revision,
                    "ccr_pool_ids": pool_ids,
                    "schema_commit": CCR_COMMIT,
                    "unsupported": ["atomic reservation", "lease admission", "reward", "approval"],
                }
            },
        }
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(task)
        proposals.append(task)
    return proposals


def cait_envelope(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "format": "vek-capacity-for-cait-v1",
        "cait_schema_commit": CAIT_COMMIT,
        "compatibility": "partial-VEK-owned-envelope",
        "capacity_report": report,
        "unsupported": ["CAIT arrival verdict", "growth-window", "endogenous attribution"],
        "arrival_verdict": None,
    }
