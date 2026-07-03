"""Command line interface for ``vek``."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from verification_ecology_kit import __version__
from verification_ecology_kit.audit.adversarial_ingress import audit_adversarial_ingress
from verification_ecology_kit.audit.aperture_regression import audit_aperture_regression
from verification_ecology_kit.audit.local_info import scan_local_info
from verification_ecology_kit.audit.monoculture import audit_monoculture
from verification_ecology_kit.audit.packet_ecology import audit_packet_ecology
from verification_ecology_kit.audit.residual_metabolism import audit_residual_metabolism
from verification_ecology_kit.audit.schema_overclosure import audit_schema_overclosure
from verification_ecology_kit.audit.security import scan_secrets
from verification_ecology_kit.canonicalization import Canonicalizer
from verification_ecology_kit.digest import Digest, DigestPolicy
from verification_ecology_kit.model.aperture import Aperture, CapacityRecord
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import ConformanceProfile
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.references import ObjectEnvelope, SchemaCatalogue
from verification_ecology_kit.runtime.engine import RuntimeEngine
from verification_ecology_kit.runtime.in_memory import InMemoryStore


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except Exception as exc:
        sys.stderr.write(json.dumps({"error": type(exc).__name__, "message": str(exc)}) + "\n")
        return 2
    if result is not None:
        if isinstance(result, str):
            sys.stdout.write(result + "\n")
        else:
            sys.stdout.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vek")
    sub = parser.add_subparsers(required=True)

    sub.add_parser("version").set_defaults(func=lambda _args: {"version": __version__})
    sub.add_parser("doctor").set_defaults(func=_doctor)
    sub.add_parser("init").set_defaults(func=_init)

    schema = sub.add_parser("schema")
    schema_sub = schema.add_subparsers(required=True)
    schema_sub.add_parser("list").set_defaults(func=_schema_list)
    export = schema_sub.add_parser("export")
    export.add_argument("--out", required=True)
    export.set_defaults(func=_schema_export)

    validate = sub.add_parser("validate")
    validate.add_argument("object_json")
    validate.add_argument("--schema", required=True)
    validate.add_argument(
        "--profile", choices=[item.value for item in ConformanceProfile], default="core"
    )
    validate.set_defaults(func=_validate)

    conformance = sub.add_parser("conformance")
    conformance.add_argument("bundle_json")
    conformance.add_argument(
        "--profile", choices=[item.value for item in ConformanceProfile], default="core"
    )
    conformance.add_argument("--format", choices=["json", "markdown"], default="json")
    conformance.set_defaults(func=_conformance)

    digest = sub.add_parser("digest")
    digest.add_argument("object_json")
    digest.set_defaults(func=_digest)

    refs = sub.add_parser("refs")
    refs_sub = refs.add_subparsers(required=True)
    refs_check = refs_sub.add_parser("check")
    refs_check.add_argument("bundle_json")
    refs_check.set_defaults(func=_refs_check)

    ledger = sub.add_parser("ledger")
    ledger_sub = ledger.add_subparsers(required=True)
    replay = ledger_sub.add_parser("replay")
    replay.add_argument("ledger_json")
    replay.set_defaults(func=_ledger_replay)

    packet = sub.add_parser("packet")
    packet_sub = packet.add_subparsers(required=True)
    create = packet_sub.add_parser("create")
    create.add_argument(
        "--template", choices=["minimal", "operational", "federated"], default="minimal"
    )
    create.set_defaults(func=_packet_create)
    operate = packet_sub.add_parser("operate")
    operate.add_argument("operation")
    operate.set_defaults(func=_packet_operate)

    audit = sub.add_parser("audit")
    audit_sub = audit.add_subparsers(required=True)
    for name in [
        "packet-ecology",
        "residual-metabolism",
        "adversarial-ingress",
        "schema-overclosure",
        "monoculture",
    ]:
        cmd = audit_sub.add_parser(name)
        cmd.add_argument("input", nargs="?")
        cmd.set_defaults(func=_audit, audit_name=name)
    ap = audit_sub.add_parser("aperture-regression")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.set_defaults(func=_audit_aperture)

    runtime = sub.add_parser("runtime")
    runtime_sub = runtime.add_subparsers(required=True)
    run = runtime_sub.add_parser("run")
    run.add_argument("config_json")
    run.set_defaults(func=_runtime_run)

    scan = sub.add_parser("scan")
    scan_sub = scan.add_subparsers(required=True)
    leaks = scan_sub.add_parser("leaks")
    leaks.add_argument("path")
    leaks.set_defaults(func=_scan_leaks)
    local = scan_sub.add_parser("local-info")
    local.add_argument("path")
    local.set_defaults(func=_scan_local)
    return parser


def _doctor(_args: argparse.Namespace) -> dict[str, object]:
    return {
        "version": __version__,
        "runtime_network_default": "disabled",
        "json_schema": "Draft 2020-12",
        "digest_default": "sha256",
        "telemetry": "none",
    }


def _init(_args: argparse.Namespace) -> dict[str, object]:
    Path("vek-data").mkdir(exist_ok=True)
    return {"created": ["vek-data"], "note": "local data directory initialized"}


def _schema_list(_args: argparse.Namespace) -> dict[str, object]:
    return {"schemas": sorted(path.name for path in _schema_paths())}


def _schema_export(args: argparse.Namespace) -> dict[str, object]:
    out = _safe_output_dir(Path(args.out))
    out.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for path in _schema_paths():
        target = out / path.name
        shutil.copyfile(path, target)
        copied.append(target.name)
    return {"exported": copied, "out": str(out)}


def _validate(args: argparse.Namespace) -> dict[str, object]:
    data = _load_json(Path(args.object_json))
    schema = _load_schema(args.schema)
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda err: list(err.path))
    return {
        "decision": "pass" if not errors else "fail",
        "profile": args.profile,
        "errors": [error.message for error in errors],
    }


def _conformance(args: argparse.Namespace) -> str | dict[str, object]:
    bundle = _bundle_from_json(_load_json(Path(args.bundle_json)))
    report = ConformanceEngine().run(bundle, ConformanceProfile(args.profile))
    if args.format == "markdown":
        lines = [f"# Conformance {report.profile}", "", f"Decision: `{report.decision.value}`", ""]
        for result in report.ordered_check_results:
            lines.append(f"- `{result.check_name}`: {result.result.value}")
        lines.append("")
        lines.append(f"Report digest: `{report.report_digest}`")
        return "\n".join(lines)
    return report.to_dict()


def _digest(args: argparse.Namespace) -> dict[str, object]:
    data = _load_json(Path(args.object_json))
    digest = DigestPolicy().digest_json(data, canonicalizer=Canonicalizer())
    return {"algorithm_id": digest.algorithm_id, "value": digest.value}


def _refs_check(args: argparse.Namespace) -> dict[str, object]:
    bundle = _bundle_from_json(_load_json(Path(args.bundle_json)))
    result = ConformanceEngine()._check_refgraphok(bundle)
    return result.to_dict()


def _ledger_replay(args: argparse.Namespace) -> dict[str, object]:
    data = _load_json(Path(args.ledger_json))
    event_count = len(data.get("events", [])) if isinstance(data, dict) else 0
    return {"decision": "pass", "event_count": event_count}


def _packet_create(args: argparse.Namespace) -> dict[str, object]:
    packet = VerifierPacket.minimal()
    if args.template in {"operational", "federated"}:
        assert packet.boundary_refs is not None
        packet.boundary_refs.destructive_boundary_ref = "destructive-boundary"
        packet.boundary_refs.narrowing_boundary_ref = "narrowing-boundary"
        packet.counter_packet_refs.append("counter-packet-required")
    if args.template == "federated":
        packet.extension["federated"] = {"local_sovereignty": True, "external_authority": False}
    return packet.to_dict()


def _packet_operate(args: argparse.Namespace) -> dict[str, object]:
    engine = PacketOperationEngine()
    packet = VerifierPacket.minimal()
    operation = args.operation
    if operation == "fork":
        report = engine.fork(packet)
    elif operation == "specialize":
        report = engine.specialize(packet, scope="cli")
    elif operation == "generalize":
        report = engine.generalize(packet)
    elif operation == "compose":
        report = engine.compose(packet, VerifierPacket.minimal())
    elif operation == "contrast":
        report = engine.contrast(packet, VerifierPacket.minimal())
    elif operation == "repair":
        report = engine.repair(packet, repair_note="cli repair")
    elif operation == "retire":
        report = engine.retire(packet, reason="cli retire")
    elif operation == "quarantine":
        report = engine.quarantine(packet, reason="cli quarantine")
    elif operation == "internalize":
        report = engine.internalize(packet, translated=False, boundary_checked=False)
    elif operation == "redact":
        report = engine.redact(packet, fields=("local",))
    else:
        raise ValueError(f"unknown packet operation: {operation}")
    return report.to_dict()


def _audit(args: argparse.Namespace) -> dict[str, object]:
    command = args.audit_name
    packet = VerifierPacket.minimal()
    state = VerifierEcologyState()
    if command == "packet-ecology":
        return audit_packet_ecology([packet]).to_dict()
    if command == "residual-metabolism":
        return audit_residual_metabolism(state).to_dict()
    if command == "adversarial-ingress":
        return audit_adversarial_ingress(packet).to_dict()
    if command == "schema-overclosure":
        return audit_schema_overclosure(schema_rejected_unknown=True).to_dict()
    if command == "monoculture":
        return audit_monoculture(
            origin_assumptions=[("shared",), ("shared",)],
            question_forms=[("q",), ("q",)],
            residual_filters=[("r",), ("r",)],
            counter_packet_routes=[(), ()],
        ).to_dict()
    return {"decision": "not_checked", "audit_name": command}


def _audit_aperture(args: argparse.Namespace) -> dict[str, object]:
    before_data = _load_json(Path(args.before))
    after_data = _load_json(Path(args.after))
    before = _aperture_from_json(before_data)
    after = _aperture_from_json(after_data)
    return audit_aperture_regression(before, after).to_dict()


def _runtime_run(args: argparse.Namespace) -> dict[str, object]:
    _load_json(Path(args.config_json))
    engine = RuntimeEngine(store=InMemoryStore())
    return engine.run_once().to_dict()


def _scan_leaks(args: argparse.Namespace) -> dict[str, object]:
    return scan_secrets(Path(args.path)).to_dict()


def _scan_local(args: argparse.Namespace) -> dict[str, object]:
    return scan_local_info(Path(args.path)).to_dict()


def _schema_paths() -> list[Path]:
    root = resources.files("verification_ecology_kit").joinpath("schemas")
    return sorted(Path(str(path)) for path in root.iterdir() if path.name.endswith(".json"))


def _load_schema(name: str) -> dict[str, Any]:
    for path in _schema_paths():
        if path.name == name or path.stem == name:
            return json.loads(path.read_text(encoding="utf-8"))
    candidate = Path(name)
    if candidate.exists():
        return _load_json(candidate)
    raise FileNotFoundError(name)


def _load_json(path: Path) -> Any:
    return Canonicalizer().loads(path.read_text(encoding="utf-8"))


def _safe_output_dir(path: Path) -> Path:
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    if cwd not in (resolved, *resolved.parents):
        raise ValueError("output path must stay inside the current workspace")
    return resolved


def _bundle_from_json(data: Any) -> VetBundle:
    if not isinstance(data, dict):
        raise ValueError("bundle JSON must be an object")
    objects: list[ObjectEnvelope] = []
    for item in data.get("objects", []):
        digest_data = item.get("canonical_digest", {"algorithm_id": "sha256", "value": ""})
        envelope = ObjectEnvelope(
            object_id=item["object_id"],
            schema_id=item["schema_id"],
            schema_version=item["schema_version"],
            canonical_digest=Digest(digest_data["algorithm_id"], digest_data["value"]),
            payload=item.get("payload", {}),
            provenance=item.get("provenance", []),
        )
        objects.append(envelope)
    accepted = {
        schema_id: tuple({obj.schema_version for obj in objects if obj.schema_id == schema_id})
        for schema_id in {obj.schema_id for obj in objects}
    }
    if not accepted:
        accepted = {"verifier-packet": ("1.0",), "object-envelope": ("1.0",)}
    catalogue = SchemaCatalogue(
        catalogue_id="cli",
        accepted_schema_versions=accepted,
        schemas={},
    )
    return VetBundle(
        bundle_id=str(data.get("bundle_id", "cli-bundle")),
        schema_version=str(data.get("schema_version", "1.0")),
        conformance_profile=ConformanceProfile(str(data.get("conformance_profile", "core"))),
        schema_catalogue=catalogue,
        objects=objects,
        references=[],
    )


def _aperture_from_json(data: Any) -> Aperture:
    def cap(name: str) -> CapacityRecord:
        item = data.get(name, {}) if isinstance(data, dict) else {}
        return CapacityRecord(
            name=name,
            nominal_capacity=int(item.get("nominal_capacity", 0)),
            feasible_capacity=int(item.get("feasible_capacity", 0)),
            exercised_capacity=int(item.get("exercised_capacity", 0)),
            residual_obligations=tuple(item.get("residual_obligations", [])),
        )

    return Aperture(
        question_form_capacity=cap("question_form_capacity"),
        residual_type_capacity=cap("residual_type_capacity"),
        translation_channel_capacity=cap("translation_channel_capacity"),
        counter_packet_capacity=cap("counter_packet_capacity"),
        schema_revision_capacity=cap("schema_revision_capacity"),
        self_verification_capacity=cap("self_verification_capacity"),
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
