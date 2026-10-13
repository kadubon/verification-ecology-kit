"""Versioned VEK-owned capacity evidence, with no companion authority effects."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from verification_ecology_kit import __version__
from verification_ecology_kit.capacity.checker import Snapshot, check_plan
from verification_ecology_kit.capacity.model import Contract, validate_schema

NON_CLAIMS = [
    "no execution authority",
    "no scientific truth or capability growth",
    "no empirical independence",
    "no service guarantee from observed averages",
    "no global scheduling optimum",
    "no infinite-horizon stability",
    "Python conformance-tested, not wholly formally verified",
]


def capacity_report(c: Contract, s: Snapshot, plan: dict[str, Any]) -> dict[str, Any]:
    checked = check_plan(c, s, plan)
    elapsed = Fraction(c.slot_seconds) * s.clock
    report = {
        "record_type": "vek_verification_capacity_report_v1",
        "schema_version": "1",
        "producer_version": __version__,
        "contract_digest": c.contract_digest,
        "source_digest": s.source_digest,
        "snapshot_revision": s.revision,
        "scope": c.scope,
        "evidence_basis": "declared-model",
        "time_origin": c.time_origin,
        "slot_seconds": c.slot_seconds,
        "horizon": c.horizon,
        "work_unit": c.work_unit,
        "domains": sorted({w.domain for w in c.work}),
        "planning_assumptions": [x for v in c.services for x in v.assumptions],
        "service_guaranteed_lower_envelope": None,
        "observed_service": None,
        "local_accounting": {
            "completed": len(s.completed),
            "reserved": len(s.reservations),
            "attempts": sum(s.attempts.values()),
            "consumed": s.spent,
            "unfinished": len(c.work) - len(s.completed) + len(s.followups),
            "repair": sorted(s.repair),
            "elapsed_seconds": str(elapsed),
            "descriptive_completion_rate": str(Fraction(len(s.completed), 1) / elapsed)
            if elapsed
            else None,
            "evidence_basis": "synthetic-or-declared-model",
        },
        "resources": c.to_dict()["resources"],
        "work": c.to_dict()["work"],
        "unsupported_dependence": [v.service_id for v in c.services if not v.dependence_known],
        "pending_followup_work": list(s.followups.values()),
        "forecast": checked.to_dict(),
        "search": plan["search"],
        "non_claims": NON_CLAIMS,
    }
    validate_schema("capacity-report", report)
    return report
