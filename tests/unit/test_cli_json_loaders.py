from __future__ import annotations

import pytest

from verification_ecology_kit import cli
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import Visibility


def _packet_payload() -> dict[str, object]:
    packet = VerifierPacket.minimal()
    assert packet.origin is not None
    assert packet.scope is not None
    assert packet.transformation_class is not None
    assert packet.verifier_procedure is not None
    assert packet.certification_condition is not None
    assert packet.boundary_refs is not None
    assert packet.residual_hooks is not None
    assert packet.update_profile is not None
    assert packet.circulation_status is not None

    packet.origin.traces.append("trace")
    packet.origin.lineage.append("parent")
    packet.scope.assumptions.append("assumption")
    packet.scope.applies_to.append("target")
    packet.transformation_class.allowed.append("fork")
    packet.verifier_procedure.steps.append("inspect")
    packet.certification_condition.pass_conditions.append("evidence-present")
    packet.boundary_refs.destructive_boundary_ref = "destructive"
    packet.boundary_refs.narrowing_boundary_ref = "narrowing"
    packet.boundary_refs.reachability_certificate_refs.append("reach")
    packet.update_profile.revalidation_triggers.append("schema-change")
    packet.circulation_status.visibility = Visibility.SHARED
    packet.counter_packet_refs.append("counter")
    packet.question_form = {"kind": "unit"}
    packet.extension = {"local": {"field": "value"}}
    return packet.to_dict()


def _residual_payload() -> dict[str, object]:
    return {
        "kind": "unresolved",
        "origin": "unit",
        "scope": ["scope"],
        "obligation": "route the residual",
        "payload": {"detail": "value"},
        "exposure": "informational",
        "status": "active",
        "route": {
            "owner": "owner",
            "deadline": "2999-01-01T00:00:00Z",
            "resource_quota": ["review-hour"],
            "recheck_trigger": "manual",
            "authority_effect": "informational",
            "active_follow_through": True,
        },
        "update_links": ["link"],
        "provenance": ["prov"],
        "residual_id": "res-unit",
    }


def _ref_payload() -> dict[str, object]:
    return {
        "bundle_id": "bundle",
        "object_id": "object",
        "schema_id": "verifier-packet",
        "pointer": "/payload",
        "digest_algorithm_id": "sha256",
        "digest": {"algorithm_id": "sha256", "value": "abc"},
        "intended_use": "support",
    }


def test_packet_loader_round_trips_full_payload() -> None:
    data = _packet_payload()
    data["residual_obligations"] = [_residual_payload()]

    packet = cli._packet_from_json(data)

    assert packet.packet_id == data["packet_id"]
    assert packet.origin is not None
    assert packet.origin.traces == ["trace"]
    assert packet.scope is not None
    assert packet.scope.assumptions == ["assumption"]
    assert packet.boundary_refs is not None
    assert packet.boundary_refs.reachability_certificate_refs == ["reach"]
    assert packet.residual_obligations[0].route is not None
    assert packet.residual_obligations[0].route.owner == "owner"


def test_optional_packet_sections_can_be_missing() -> None:
    assert cli._origin_from_json(None) is None
    assert cli._scope_from_json(None) is None
    assert cli._transformation_from_json(None) is None
    assert cli._procedure_from_json(None) is None
    assert cli._certification_condition_from_json(None) is None
    assert cli._boundary_refs_from_json(None) is None
    assert cli._residual_hooks_from_json(None) is None
    assert cli._update_profile_from_json(None) is None
    assert cli._circulation_status_from_json(None) is None
    assert cli._route_from_json(None) is None
    assert cli._digest_from_json(None) is None
    assert cli._digest_from_json({"algorithm_id": "sha256", "value": ""}) is None


def test_ledger_loader_accepts_dict_residuals_and_events() -> None:
    event = {
        "kind": "add",
        "source_residuals": [],
        "target_residuals": ["res-unit"],
        "justification": "unit",
        "pre_state_digest": "",
        "post_state_digest": "",
        "actor_authority_ref": "tester",
        "policy_id": "policy",
        "event_id": "event",
        "clock_model": "total_order",
        "conflict_policy": "preserve_or_residualize",
        "predecessor_event_id": "previous",
        "provenance": ["prov"],
    }

    ledger = cli._ledger_from_json(
        {
            "policy_id": "policy",
            "residuals": {"res-unit": _residual_payload()},
            "events": [event],
        }
    )

    assert ledger.policy_id == "policy"
    assert list(ledger.residuals) == ["res-unit"]
    assert ledger.events[0].predecessor_event_id == "previous"


def test_bundle_loader_restores_catalogue_refs_and_records() -> None:
    bundle = cli._bundle_from_json(
        {
            "bundle_id": "bundle",
            "schema_version": "1.0",
            "conformance_profile": "operational",
            "schema_catalogue": {
                "catalogue_id": "catalogue",
                "accepted_schema_versions": {"verifier-packet": ["1.0"]},
                "schemas": {"verifier-packet": {}},
            },
            "objects": [
                {
                    "object_id": "object",
                    "schema_id": "verifier-packet",
                    "schema_version": "1.0",
                    "canonical_digest": {"algorithm_id": "sha256", "value": "abc"},
                    "payload": _packet_payload(),
                    "provenance": ["prov"],
                    "status_ref": _ref_payload(),
                    "residual_refs": [_ref_payload()],
                }
            ],
            "references": [_ref_payload()],
            "residual_ledger": {"residuals": [_residual_payload()], "events": []},
            "authority_decisions": [{"decision": "allow"}],
            "judgment_records": [{"JValid_result": "pass"}],
            "provenance": ["bundle-prov"],
        }
    )

    assert bundle.bundle_id == "bundle"
    assert bundle.schema_catalogue.catalogue_id == "catalogue"
    assert bundle.objects[0].status_ref is not None
    assert bundle.objects[0].residual_refs
    assert bundle.references
    assert bundle.authority_decisions == [{"decision": "allow"}]


def test_audit_input_loaders_accept_state_and_bundle_shapes() -> None:
    packet = _packet_payload()
    state = cli._state_from_audit_input(
        {
            "packet_population": {"packet": packet},
            "residual_ledger": {"residuals": [_residual_payload()], "events": []},
            "archive": {"raw": True},
            "reusable_intelligence_capital": {"packet": "value"},
        }
    )
    assert state.packet_population
    assert state.archive == {"raw": True}
    assert state.reusable_intelligence_capital == {"packet": "value"}

    packets = cli._packets_from_audit_input(
        {
            "objects": [
                {
                    "object_id": "object",
                    "schema_id": "verifier-packet",
                    "schema_version": "1.0",
                    "payload": packet,
                }
            ]
        }
    )
    assert len(packets) == 1


def test_loader_errors_are_explicit() -> None:
    with pytest.raises(ValueError, match="expected a list"):
        cli._string_list("not-a-list")
    with pytest.raises(ValueError, match="ledger residuals"):
        cli._ledger_from_json({"residuals": "not-a-list"})
    with pytest.raises(ValueError, match="ledger events"):
        cli._ledger_from_json({"events": "not-a-list"})
    with pytest.raises(ValueError, match="audit input did not contain"):
        cli._packets_from_audit_input({"objects": []})
