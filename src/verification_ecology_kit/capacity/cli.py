"""CLI equivalents of the experimental capacity profile's Python operations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from verification_ecology_kit.capacity.baselines import compare
from verification_ecology_kit.capacity.checker import check_plan
from verification_ecology_kit.capacity.examples import NAMES, run_example
from verification_ecology_kit.capacity.interchange import cait_envelope, ccr_proposals
from verification_ecology_kit.capacity.model import Contract, require
from verification_ecology_kit.capacity.report import capacity_report
from verification_ecology_kit.capacity.runtime import CapacityRuntime
from verification_ecology_kit.runtime.json_store import JsonStore


def register(sub: Any) -> None:
    family = sub.add_parser("capacity").add_subparsers(dest="capacity_command", required=True)
    example = family.add_parser("example")
    example.add_argument("name", choices=NAMES)
    example.set_defaults(func=lambda args: run_example(args.name))
    for name in (
        "inspect",
        "plan",
        "check-plan",
        "apply-local",
        "ingest",
        "replay",
        "compare",
        "export",
    ):
        command = family.add_parser(name)
        command.add_argument("contract")
        command.add_argument("--store", required=True)
        if name in {"check-plan", "apply-local"}:
            command.add_argument("--plan", required=True)
        if name == "ingest":
            command.add_argument("--event", required=True)
        if name == "apply-local":
            command.add_argument("--event-id", required=True)
        if name == "export":
            command.add_argument("--format", choices=["vek", "ccr", "cait"], default="vek")
            command.add_argument("--ccr-revision")
            command.add_argument("--ccr-pool", action="append", default=[])
        command.set_defaults(func=execute)


def load(path: str) -> dict[str, Any]:
    target = Path(path)
    require(target.stat().st_size <= 2_000_000, "capacity input size bound exceeded")
    value = json.loads(target.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "capacity record must be an object")
    return value


def execute(args: argparse.Namespace) -> dict[str, Any]:
    c = Contract.from_dict(load(args.contract))
    runtime = CapacityRuntime(JsonStore(Path(args.store)), c)
    command = args.capacity_command
    if command in {"inspect", "replay"}:
        return runtime.inspect().to_dict()
    if command == "compare":
        return compare(c, runtime.inspect())
    if command == "plan":
        value = runtime.plan()
        return value
    if command == "check-plan":
        return check_plan(c, runtime.inspect(), load(args.plan)).to_dict()
    if command == "apply-local":
        return runtime.event("apply", load(args.plan), args.event_id).to_dict()
    if command == "ingest":
        return runtime.update(load(args.event)).to_dict()
    if args.format == "ccr":
        return {
            "proposals": ccr_proposals(c, revision=args.ccr_revision, pool_ids=args.ccr_pool),
            "unallocated_followups": list(runtime.inspect().followups.values()),
            "followup_limitation": "new artifact checks require registered cost/quality bounds",
        }
    report = capacity_report(c, runtime.inspect(), runtime.plan())
    return cait_envelope(report) if args.format == "cait" else report
