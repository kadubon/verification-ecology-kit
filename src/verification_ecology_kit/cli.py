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
from verification_ecology_kit.model import serde as model_serde
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.packets import (
    VerifierPacket,
)
from verification_ecology_kit.model.records import (
    ConformanceProfile,
)
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.references import ObjectRef
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
    return _exit_code(result)


def _exit_code(result: object) -> int:
    if not isinstance(result, dict):
        return 0
    decision = result.get("decision")
    if decision in {"fail", "reject", "quarantine"}:
        return 1
    status = result.get("result")
    if status == "fail":
        return 1
    if result.get("support_blocking_failures"):
        return 1
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
    operate.add_argument(
        "operation",
        choices=[
            "fork",
            "specialize",
            "generalize",
            "compose",
            "contrast",
            "repair",
            "retire",
            "quarantine",
            "internalize",
            "redact",
        ],
    )
    operate.add_argument("inputs", nargs="+", help="Packet JSON files consumed by the operation.")
    operate.add_argument("--out", required=True, help="Where to write the output packet JSON.")
    operate.add_argument("--scope", default="cli", help="Scope appended by specialize.")
    operate.add_argument("--repair-note", default="cli repair", help="Repair note for repair.")
    operate.add_argument(
        "--reason", default="cli operation", help="Reason for fork/retire/quarantine."
    )
    operate.add_argument(
        "--translated",
        choices=["true", "false"],
        default="false",
        help="Whether an internalize input has been translated.",
    )
    operate.add_argument(
        "--boundary-checked",
        choices=["true", "false"],
        default="false",
        help="Whether an internalize input has completed boundary checks.",
    )
    operate.add_argument(
        "--field",
        action="append",
        default=[],
        help="Extension field to remove during redact. May be passed multiple times.",
    )
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
        cmd.add_argument("input")
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
    ledger = _ledger_from_json(_load_json(Path(args.ledger_json)))
    trace = ledger.trace_ok()
    return {
        "decision": "pass" if trace.passed else "fail",
        "event_count": len(ledger.events),
        "trace": trace.to_dict(),
    }


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
    packets = [_packet_from_json(_load_json(Path(path))) for path in args.inputs]
    operation = args.operation
    if operation == "fork":
        _expect_input_count(packets, 1, operation)
        report = engine.fork(packets[0], reason=str(args.reason))
    elif operation == "specialize":
        _expect_input_count(packets, 1, operation)
        report = engine.specialize(packets[0], scope=str(args.scope))
    elif operation == "generalize":
        _expect_input_count(packets, 1, operation)
        report = engine.generalize(packets[0])
    elif operation == "compose":
        _expect_input_count(packets, 2, operation)
        report = engine.compose(packets[0], packets[1])
    elif operation == "contrast":
        _expect_input_count(packets, 2, operation)
        report = engine.contrast(packets[0], packets[1])
    elif operation == "repair":
        _expect_input_count(packets, 1, operation)
        report = engine.repair(packets[0], repair_note=str(args.repair_note))
    elif operation == "retire":
        _expect_input_count(packets, 1, operation)
        report = engine.retire(packets[0], reason=str(args.reason))
    elif operation == "quarantine":
        _expect_input_count(packets, 1, operation)
        report = engine.quarantine(packets[0], reason=str(args.reason))
    elif operation == "internalize":
        _expect_input_count(packets, 1, operation)
        report = engine.internalize(
            packets[0],
            translated=args.translated == "true",
            boundary_checked=args.boundary_checked == "true",
        )
    elif operation == "redact":
        _expect_input_count(packets, 1, operation)
        fields = tuple(str(field) for field in args.field) or ("local",)
        report = engine.redact(packets[0], fields=fields)
    else:
        raise ValueError(f"unknown packet operation: {operation}")
    if report.output_packet is not None:
        _write_json(_safe_output_file(Path(args.out)), report.output_packet.to_dict())
    result = report.to_dict()
    result["output_path"] = str(Path(args.out))
    return result


def _audit(args: argparse.Namespace) -> dict[str, object]:
    command = args.audit_name
    data = _load_json(Path(args.input))
    if command == "packet-ecology":
        return audit_packet_ecology(_packets_from_audit_input(data)).to_dict()
    if command == "residual-metabolism":
        return audit_residual_metabolism(_state_from_audit_input(data)).to_dict()
    if command == "adversarial-ingress":
        return audit_adversarial_ingress(_packet_from_json(data)).to_dict()
    if command == "schema-overclosure":
        if not isinstance(data, dict):
            raise ValueError("schema-overclosure audit input must be an object")
        suppressed = data.get("suppressed_residuals", ())
        if not isinstance(suppressed, list | tuple):
            raise ValueError("suppressed_residuals must be a list")
        return audit_schema_overclosure(
            schema_rejected_unknown=bool(data.get("schema_rejected_unknown", False)),
            suppressed_residuals=tuple(str(item) for item in suppressed),
            dashboard_hid_component_failure=bool(
                data.get("dashboard_hid_component_failure", False)
            ),
            incompatible_residuals_suppressed=tuple(
                str(item) for item in data.get("incompatible_residuals_suppressed", ())
            ),
            anti_overclosure_rigid_labels=bool(data.get("anti_overclosure_rigid_labels", False)),
            field_rename_without_migration_witness=bool(
                data.get("field_rename_without_migration_witness", False)
            ),
            required_field_added_without_migration_residual=bool(
                data.get("required_field_added_without_migration_residual", False)
            ),
            additional_properties_false_without_escape_hatch=bool(
                data.get("additional_properties_false_without_escape_hatch", False)
            ),
        ).to_dict()
    if command == "monoculture":
        packets = _packets_from_audit_input(data)
        return audit_monoculture(
            origin_assumptions=[
                tuple(packet.scope.assumptions)
                if packet.scope is not None and packet.scope.assumptions
                else ("unspecified",)
                for packet in packets
            ],
            question_forms=[
                tuple(str(key) for key in sorted(packet.question_form)) or ("unspecified",)
                for packet in packets
            ],
            residual_filters=[
                tuple(sorted({residual.kind.value for residual in packet.residual_obligations}))
                or ("none",)
                for packet in packets
            ],
            counter_packet_routes=[
                tuple(packet.counter_packet_refs) if packet.counter_packet_refs else ()
                for packet in packets
            ],
        ).to_dict()
    return {"decision": "not_checked", "audit_name": command}


def _audit_aperture(args: argparse.Namespace) -> dict[str, object]:
    before_data = _load_json(Path(args.before))
    after_data = _load_json(Path(args.after))
    before = _aperture_from_json(before_data)
    after = _aperture_from_json(after_data)
    return audit_aperture_regression(before, after).to_dict()


def _runtime_run(args: argparse.Namespace) -> dict[str, object]:
    config = _load_json(Path(args.config_json))
    state = VerifierEcologyState()
    if isinstance(config, dict) and "state" in config:
        state = _state_from_audit_input(config["state"])
    engine = RuntimeEngine(store=InMemoryStore(state=state))
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


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_output_dir(path: Path) -> Path:
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    if cwd not in (resolved, *resolved.parents):
        raise ValueError("output path must stay inside the current workspace")
    return resolved


def _safe_output_file(path: Path) -> Path:
    resolved = path.resolve()
    cwd = Path.cwd().resolve()
    if cwd not in resolved.parents:
        raise ValueError("output path must stay inside the current workspace")
    if resolved.exists() and resolved.is_dir():
        raise ValueError("output path must be a file")
    return resolved


def _expect_input_count(
    packets: list[VerifierPacket],
    expected: int,
    operation: str,
) -> None:
    if len(packets) != expected:
        raise ValueError(f"{operation} expects {expected} packet input(s), got {len(packets)}")


def _as_dict(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _optional_dict(value: Any, *, name: str) -> dict[str, Any] | None:
    if value is None:
        return None
    return _as_dict(value, name=name)


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list | tuple):
        raise ValueError("expected a list of strings")
    return [str(item) for item in value]


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(_string_list(value))


def _dict_value(value: Any, *, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    return _as_dict(value, name=name)


_packet_from_json = model_serde.load_packet
_origin_from_json = model_serde.origin_from_json
_scope_from_json = model_serde.scope_from_json
_transformation_from_json = model_serde.transformation_from_json
_procedure_from_json = model_serde.procedure_from_json
_certification_condition_from_json = model_serde.certification_condition_from_json
_boundary_refs_from_json = model_serde.boundary_refs_from_json
_residual_hooks_from_json = model_serde.residual_hooks_from_json
_update_profile_from_json = model_serde.update_profile_from_json
_circulation_status_from_json = model_serde.circulation_status_from_json
_anti_overclosure_from_json = model_serde.anti_overclosure_from_json
_ecological_invariants_from_json = model_serde.ecological_invariants_from_json
_residual_liveness_from_json = model_serde.residual_liveness_from_json
_route_from_json = model_serde.load_residual_route
_residual_from_json = model_serde.load_residual
_ledger_event_from_json = model_serde.load_ledger_event
_ledger_from_json = model_serde.load_ledger
_packets_from_audit_input = model_serde.packets_from_audit_input
_state_from_audit_input = model_serde.load_audit_state
_aperture_from_json = model_serde.load_aperture


def _serde_object_ref_from_json(data: Any) -> ObjectRef:
    return model_serde.load_object_ref(data)


def _serde_bundle_from_json(data: Any) -> VetBundle:
    return model_serde.load_vet_bundle(data)


def _serde_optional_digest(data: Any) -> Digest | None:
    if data is None:
        return None
    digest = model_serde.load_digest(data)
    if not digest.value:
        return None
    return digest


_object_ref_from_json = _serde_object_ref_from_json
_bundle_from_json = _serde_bundle_from_json
_digest_from_json = _serde_optional_digest


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
