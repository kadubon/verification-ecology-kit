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
from verification_ecology_kit.ids import new_id
from verification_ecology_kit.model.aperture import Aperture, CapacityRecord
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.ledger import LedgerEvent, ResidualLedger
from verification_ecology_kit.model.packets import (
    AntiOverclosure,
    BoundaryRefs,
    CertificationCondition,
    CirculationStatus,
    EcologicalInvariants,
    PacketOrigin,
    PacketScope,
    ResidualHooks,
    ResidualLivenessPolicy,
    TransformationClass,
    UpdateProfile,
    VerifierPacket,
    VerifierProcedure,
)
from verification_ecology_kit.model.records import (
    ConformanceProfile,
    LedgerStatus,
    OriginKind,
    ResidualKind,
    ResidualMetabolismRoute,
    TrustStatus,
    Visibility,
)
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute
from verification_ecology_kit.operations.base import PacketOperationEngine
from verification_ecology_kit.references import ObjectEnvelope, ObjectRef, SchemaCatalogue
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


def _packet_from_json(data: Any) -> VerifierPacket:
    data = _as_dict(data, name="packet JSON")
    packet = VerifierPacket(
        origin=_origin_from_json(_optional_dict(data.get("origin"), name="origin")),
        scope=_scope_from_json(_optional_dict(data.get("scope"), name="scope")),
        transformation_class=_transformation_from_json(
            _optional_dict(data.get("transformation_class"), name="transformation_class")
        ),
        verifier_procedure=_procedure_from_json(
            _optional_dict(data.get("verifier_procedure"), name="verifier_procedure")
        ),
        certification_condition=_certification_condition_from_json(
            _optional_dict(data.get("certification_condition"), name="certification_condition")
        ),
        boundary_refs=_boundary_refs_from_json(
            _optional_dict(data.get("boundary_refs"), name="boundary_refs")
        ),
        residual_hooks=_residual_hooks_from_json(
            _optional_dict(data.get("residual_hooks"), name="residual_hooks")
        ),
        update_profile=_update_profile_from_json(
            _optional_dict(data.get("update_profile"), name="update_profile")
        ),
        circulation_status=_circulation_status_from_json(
            _optional_dict(data.get("circulation_status"), name="circulation_status")
        ),
        packet_id=str(data.get("packet_id") or new_id("pkt")),
        question_form=_dict_value(data.get("question_form"), name="question_form"),
        extension=_dict_value(data.get("extension"), name="extension"),
        residual_obligations=[
            _residual_from_json(item) for item in data.get("residual_obligations", [])
        ],
        counter_packet_refs=_string_list(data.get("counter_packet_refs")),
        anti_overclosure=_anti_overclosure_from_json(
            _optional_dict(data.get("anti_overclosure"), name="anti_overclosure")
        ),
        ecological_invariants=_ecological_invariants_from_json(
            _optional_dict(data.get("ecological_invariants"), name="ecological_invariants")
        ),
        residual_liveness=_residual_liveness_from_json(
            _optional_dict(data.get("residual_liveness"), name="residual_liveness")
        ),
    )
    packet.ensure_core_accountability()
    return packet


def _origin_from_json(data: dict[str, Any] | None) -> PacketOrigin | None:
    if data is None:
        return None
    return PacketOrigin(
        created_from=OriginKind(str(data.get("created_from", OriginKind.HUMAN_SPECIFICATION))),
        traces=_string_list(data.get("traces")),
        lineage=_string_list(data.get("lineage")),
        parent_packets=_string_list(data.get("parent_packets")),
        inherited_residuals=_string_list(data.get("inherited_residuals")),
        inherited_boundaries=_string_list(data.get("inherited_boundaries")),
        inherited_overclosure_exposures=_string_list(data.get("inherited_overclosure_exposures")),
        unresolved_origin_residuals=_string_list(data.get("unresolved_origin_residuals")),
    )


def _scope_from_json(data: dict[str, Any] | None) -> PacketScope | None:
    if data is None:
        return None
    return PacketScope(
        applies_to=_string_list(data.get("applies_to")),
        excludes=_string_list(data.get("excludes")),
        assumptions=_string_list(data.get("assumptions")),
        unvalidated_assumptions=_string_list(data.get("unvalidated_assumptions")),
        known_misuse_contexts=_string_list(data.get("known_misuse_contexts")),
        known_invalid_scopes=_string_list(data.get("known_invalid_scopes")),
    )


def _transformation_from_json(data: dict[str, Any] | None) -> TransformationClass | None:
    if data is None:
        return None
    return TransformationClass(
        allowed=_string_list(data.get("allowed")),
        forbidden=_string_list(data.get("forbidden")),
        transfer_conditions=_string_list(data.get("transfer_conditions")),
        self_modification_roles=_string_list(data.get("self_modification_roles")),
    )


def _procedure_from_json(data: dict[str, Any] | None) -> VerifierProcedure | None:
    if data is None:
        return None
    return VerifierProcedure(
        steps=_string_list(data.get("steps")),
        tests=_string_list(data.get("tests")),
        proof_obligations=_string_list(data.get("proof_obligations")),
        statistical_methods=_string_list(data.get("statistical_methods")),
        stochastic_methods=_string_list(data.get("stochastic_methods")),
        tool_dependencies=_string_list(data.get("tool_dependencies")),
        evaluator_versions=_string_list(data.get("evaluator_versions")),
        counterexample_search=_string_list(data.get("counterexample_search")),
        boundary_checks=_string_list(data.get("boundary_checks")),
    )


def _certification_condition_from_json(
    data: dict[str, Any] | None,
) -> CertificationCondition | None:
    if data is None:
        return None
    return CertificationCondition(
        pass_conditions=_string_list(data.get("pass_conditions")),
        fail_conditions=_string_list(data.get("fail_conditions")),
        quarantine_conditions=_string_list(data.get("quarantine_conditions")),
        residualization_conditions=_string_list(data.get("residualization_conditions")),
        promotion_conditions=_string_list(data.get("promotion_conditions")),
    )


def _boundary_refs_from_json(data: dict[str, Any] | None) -> BoundaryRefs | None:
    if data is None:
        return None
    return BoundaryRefs(
        destructive_boundary_ref=str(data.get("destructive_boundary_ref", "")),
        narrowing_boundary_ref=str(data.get("narrowing_boundary_ref", "")),
        reachability_certificate_refs=_string_list(data.get("reachability_certificate_refs")),
        inherited_boundary_refs=_string_list(data.get("inherited_boundary_refs")),
    )


def _residual_hooks_from_json(data: dict[str, Any] | None) -> ResidualHooks | None:
    if data is None:
        return None
    return ResidualHooks(
        unresolved_residual_refs=_string_list(data.get("unresolved_residual_refs")),
        missing_core_fields=_string_list(data.get("missing_core_fields")),
        missing_fields=_string_list(data.get("missing_fields")),
        conflict_residual_refs=_string_list(data.get("conflict_residual_refs")),
        merge_loss_residual_refs=_string_list(data.get("merge_loss_residual_refs")),
        redaction_residual_refs=_string_list(data.get("redaction_residual_refs")),
    )


def _update_profile_from_json(data: dict[str, Any] | None) -> UpdateProfile | None:
    if data is None:
        return None
    return UpdateProfile(
        repair_conditions=_string_list(data.get("repair_conditions")),
        retirement_conditions=_string_list(data.get("retirement_conditions")),
        revalidation_triggers=_string_list(data.get("revalidation_triggers")),
        scope_drift_triggers=_string_list(data.get("scope_drift_triggers")),
        contamination_triggers=_string_list(data.get("contamination_triggers")),
        rollback_hooks=_string_list(data.get("rollback_hooks")),
    )


def _circulation_status_from_json(data: dict[str, Any] | None) -> CirculationStatus | None:
    if data is None:
        return None
    return CirculationStatus(
        visibility=Visibility(str(data.get("visibility", Visibility.PRIVATE))),
        trust_status=TrustStatus(str(data.get("trust_status", TrustStatus.LOCAL))),
        local_internalization_status=str(data.get("local_internalization_status", "local")),
        quarantine_ref=str(data.get("quarantine_ref", "")),
        translation_residual_refs=_string_list(data.get("translation_residual_refs")),
        redaction_residual_refs=_string_list(data.get("redaction_residual_refs")),
        boundary_check_refs=_string_list(data.get("boundary_check_refs")),
    )


def _anti_overclosure_from_json(data: dict[str, Any] | None) -> AntiOverclosure:
    if data is None:
        return AntiOverclosure()
    return AntiOverclosure(
        unknowns_to_preserve=_string_list(data.get("unknowns_to_preserve")),
        future_candidates_may_narrow=bool(data.get("future_candidates_may_narrow", False)),
        question_forms_may_suppress=bool(data.get("question_forms_may_suppress", False)),
        schema_overclosure_residuals=_string_list(data.get("schema_overclosure_residuals")),
        lineage_laundering_checks=_string_list(data.get("lineage_laundering_checks")),
    )


def _ecological_invariants_from_json(data: dict[str, Any] | None) -> EcologicalInvariants:
    if data is None:
        return EcologicalInvariants()
    return EcologicalInvariants(
        preserve_origin=bool(data.get("preserve_origin", True)),
        preserve_scope=bool(data.get("preserve_scope", True)),
        preserve_residuals=bool(data.get("preserve_residuals", True)),
        preserve_boundaries=bool(data.get("preserve_boundaries", True)),
        preserve_counter_packet_route=bool(data.get("preserve_counter_packet_route", True)),
        preserve_aperture=bool(data.get("preserve_aperture", True)),
    )


def _residual_liveness_from_json(data: dict[str, Any] | None) -> ResidualLivenessPolicy:
    if data is None:
        return ResidualLivenessPolicy()
    return ResidualLivenessPolicy(
        owner=str(data.get("owner", "")),
        deadline=str(data.get("deadline", "")),
        resource_quota=_string_list(data.get("resource_quota")),
        recheck_trigger=str(data.get("recheck_trigger", "")),
        preserved_unknown_route=str(data.get("preserved_unknown_route", "")),
    )


def _route_from_json(data: Any) -> ResidualRoute | None:
    if data is None:
        return None
    data = _as_dict(data, name="residual route")
    return ResidualRoute(
        owner=str(data.get("owner", "")),
        deadline=str(data.get("deadline", "")),
        resource_quota=_string_tuple(data.get("resource_quota")),
        recheck_trigger=str(data.get("recheck_trigger", "")),
        route_type=ResidualMetabolismRoute(
            str(data.get("route_type", ResidualMetabolismRoute.EXPLICIT_PRESERVED_UNKNOWN))
        ),
        authority_effect=str(data.get("authority_effect", "informational")),
        active_follow_through=bool(data.get("active_follow_through", True)),
    )


def _residual_from_json(data: Any) -> ResidualRecord:
    data = _as_dict(data, name="residual")
    return ResidualRecord(
        kind=ResidualKind(str(data.get("kind", ResidualKind.UNRESOLVED))),
        origin=str(data.get("origin", "")),
        scope=_string_tuple(data.get("scope")),
        obligation=str(data.get("obligation", "")),
        payload=_dict_value(data.get("payload"), name="payload"),
        exposure=str(data.get("exposure", "informational")),
        status=LedgerStatus(str(data.get("status", LedgerStatus.ACTIVE))),
        route=_route_from_json(data.get("route")),
        update_links=_string_tuple(data.get("update_links")),
        provenance=_string_tuple(data.get("provenance")),
        residual_id=str(data.get("residual_id") or new_id("res")),
    )


def _ledger_event_from_json(data: Any) -> LedgerEvent:
    data = _as_dict(data, name="ledger event")
    predecessor = data.get("predecessor_event_id")
    return LedgerEvent(
        kind=str(data.get("kind", "import")),
        source_residuals=_string_tuple(data.get("source_residuals")),
        target_residuals=_string_tuple(data.get("target_residuals")),
        justification=str(data.get("justification", "imported event")),
        pre_state_digest=str(data.get("pre_state_digest", "")),
        post_state_digest=str(data.get("post_state_digest", "")),
        actor_authority_ref=str(data.get("actor_authority_ref", "import")),
        policy_id=str(data.get("policy_id", "vet-ledger-policy-v1")),
        event_id=str(data.get("event_id") or new_id("le")),
        clock_model=str(data.get("clock_model", "total_order")),
        conflict_policy=str(data.get("conflict_policy", "preserve_or_residualize")),
        predecessor_event_id=str(predecessor) if predecessor is not None else None,
        provenance=_string_tuple(data.get("provenance")),
        event_payload=_dict_value(data.get("event_payload"), name="event_payload"),
    )


def _ledger_from_json(data: Any) -> ResidualLedger:
    data = _as_dict(data, name="ledger")
    ledger = ResidualLedger(policy_id=str(data.get("policy_id", "vet-ledger-policy-v1")))
    residuals = data.get("residuals", [])
    if isinstance(residuals, dict):
        items = list(residuals.values())
    elif isinstance(residuals, list | tuple):
        items = list(residuals)
    else:
        raise ValueError("ledger residuals must be an object or list")
    for item in items:
        residual = _residual_from_json(item)
        ledger.residuals[residual.residual_id] = residual
    events = data.get("events", [])
    if not isinstance(events, list | tuple):
        raise ValueError("ledger events must be a list")
    ledger.events = [_ledger_event_from_json(item) for item in events]
    return ledger


def _packets_from_audit_input(data: Any) -> list[VerifierPacket]:
    if isinstance(data, list | tuple):
        packets = [_packet_from_json(item) for item in data]
    elif isinstance(data, dict) and isinstance(data.get("packets"), list | tuple):
        packets = [_packet_from_json(item) for item in data["packets"]]
    elif isinstance(data, dict) and isinstance(data.get("packet_population"), dict):
        population = _as_dict(data["packet_population"], name="packet_population")
        packets = [_packet_from_json(item) for item in population.values()]
    elif isinstance(data, dict) and isinstance(data.get("objects"), list | tuple):
        packets = [
            _packet_from_json(_as_dict(item, name="object").get("payload", {}))
            for item in data["objects"]
            if _as_dict(item, name="object").get("schema_id") == "verifier-packet"
        ]
    else:
        packets = [_packet_from_json(data)]
    if not packets:
        raise ValueError("audit input did not contain any verifier packets")
    return packets


def _state_from_audit_input(data: Any) -> VerifierEcologyState:
    state = VerifierEcologyState()
    if not isinstance(data, dict):
        state.add_packet(_packet_from_json(data))
        return state
    if "residual_ledger" in data:
        state.residual_ledger = _ledger_from_json(data["residual_ledger"])
    elif "residuals" in data or "events" in data:
        state.residual_ledger = _ledger_from_json(data)
    for packet in _packets_from_audit_input(data) if _contains_packet_input(data) else []:
        state.packet_population[packet.packet_id] = packet
    archive = data.get("archive")
    if isinstance(archive, dict):
        state.archive = archive
    capital = data.get("reusable_intelligence_capital")
    if isinstance(capital, dict):
        state.reusable_intelligence_capital = capital
    return state


def _contains_packet_input(data: dict[str, Any]) -> bool:
    return any(key in data for key in ("packets", "packet_population", "objects", "packet_id"))


def _digest_from_json(data: Any) -> Digest | None:
    if data is None:
        return None
    data = _as_dict(data, name="digest")
    value = str(data.get("value", ""))
    if not value:
        return None
    return Digest(str(data.get("algorithm_id", "sha256")), value)


def _object_ref_from_json(data: Any) -> ObjectRef:
    data = _as_dict(data, name="object reference")
    digest = _digest_from_json(data.get("digest"))
    digest_algorithm_id = str(data.get("digest_algorithm_id", "sha256"))
    if digest is not None:
        digest_algorithm_id = digest.algorithm_id
    return ObjectRef(
        bundle_id=str(data.get("bundle_id", "")),
        object_id=str(data.get("object_id", "")),
        schema_id=str(data.get("schema_id", "")),
        pointer=str(data.get("pointer", "")),
        digest_algorithm_id=digest_algorithm_id,
        digest=digest,
        intended_use=str(data.get("intended_use", "support")),
    )


def _bundle_from_json(data: Any) -> VetBundle:
    if not isinstance(data, dict):
        raise ValueError("bundle JSON must be an object")
    objects: list[ObjectEnvelope] = []
    for item in data.get("objects", []):
        item = _as_dict(item, name="object envelope")
        digest_data = item.get("canonical_digest", {"algorithm_id": "sha256", "value": ""})
        digest = _digest_from_json(digest_data) or Digest("sha256", "")
        envelope = ObjectEnvelope(
            object_id=str(item["object_id"]),
            schema_id=str(item["schema_id"]),
            schema_version=str(item["schema_version"]),
            canonical_digest=digest,
            payload=_dict_value(item.get("payload"), name="payload"),
            provenance=_string_list(item.get("provenance")),
            status_ref=_object_ref_from_json(item["status_ref"])
            if item.get("status_ref") is not None
            else None,
            residual_refs=[_object_ref_from_json(ref) for ref in item.get("residual_refs", [])],
        )
        objects.append(envelope)
    catalogue_data = data.get("schema_catalogue", {})
    if catalogue_data is None:
        catalogue_data = {}
    catalogue_data = _as_dict(catalogue_data, name="schema_catalogue")
    accepted_raw = catalogue_data.get("accepted_schema_versions", {})
    accepted: dict[str, tuple[str, ...]] = {}
    if isinstance(accepted_raw, dict):
        for schema_id, versions in accepted_raw.items():
            accepted[str(schema_id)] = _string_tuple(versions)
    if not accepted:
        accepted = {
            schema_id: tuple(
                sorted({obj.schema_version for obj in objects if obj.schema_id == schema_id})
            )
            for schema_id in {obj.schema_id for obj in objects}
        }
    if not accepted:
        accepted = {"verifier-packet": ("1.0",), "object-envelope": ("1.0",)}
    schemas_raw = catalogue_data.get("schemas", {})
    schemas: dict[str, dict[str, Any]] = {}
    if isinstance(schemas_raw, dict):
        for schema_id, schema in schemas_raw.items():
            if isinstance(schema, dict):
                schemas[str(schema_id)] = schema
    catalogue = SchemaCatalogue(
        catalogue_id=str(catalogue_data.get("catalogue_id", "cli")),
        accepted_schema_versions=accepted,
        schemas=schemas,
    )
    return VetBundle(
        bundle_id=str(data.get("bundle_id", "cli-bundle")),
        schema_version=str(data.get("schema_version", "1.0")),
        conformance_profile=ConformanceProfile(str(data.get("conformance_profile", "core"))),
        schema_catalogue=catalogue,
        objects=objects,
        references=[_object_ref_from_json(ref) for ref in data.get("references", [])],
        residual_ledger=_ledger_from_json(data.get("residual_ledger", {})),
        authority_decisions=list(data.get("authority_decisions", [])),
        judgment_records=list(data.get("judgment_records", [])),
        provenance=_string_list(data.get("provenance")),
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
