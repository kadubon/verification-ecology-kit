from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model import serde
from verification_ecology_kit.model.ecology_state import VerifierEcologyState
from verification_ecology_kit.model.judgments import JudgmentRecord
from verification_ecology_kit.model.ledger import ResidualLedger
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.reachability import (
    CounterexampleChannel,
    ReachabilityCertificate,
)
from verification_ecology_kit.model.records import LifecycleStatus, ResidualKind
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute, SoundGapResidual


def test_model_serde_packet_ledger_and_state_round_trip() -> None:
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
    packet.origin.unresolved_origin_residuals.append("origin-residual")
    packet.scope.known_invalid_scopes.append("invalid")
    packet.transformation_class.self_modification_roles.append("repair")
    packet.verifier_procedure.boundary_checks.append("boundary")
    packet.certification_condition.promotion_conditions.append("promote")
    packet.boundary_refs.reachability_certificate_refs.append("reach")
    packet.residual_hooks.merge_loss_residual_refs.append("merge-loss")
    packet.update_profile.rollback_hooks.append("rollback")
    packet.circulation_status.boundary_check_refs.append("boundary-check")
    packet.anti_overclosure.unknowns_to_preserve.append("unknown")
    packet.ecological_invariants.preserve_aperture = False
    packet.residual_liveness.owner = "owner"
    packet.residual_liveness.resource_quota.append("1h")
    packet.counter_packet_refs.append("counter")
    residual = ResidualRecord(
        ResidualKind.UNRESOLVED,
        "origin",
        ("scope",),
        "route",
        route=ResidualRoute(
            "owner",
            (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            ("1h",),
            "daily",
        ),
    )
    packet.residual_obligations.append(residual)

    ledger = ResidualLedger()
    ledger.add(residual, justification="round trip")
    state = VerifierEcologyState(residual_ledger=ledger)
    state.add_packet(packet)
    state.archive = {"raw": True}
    state.reusable_intelligence_capital = {"packet": "value"}

    loaded = serde.ecology_state_from_json(state.to_dict())

    assert packet.packet_id in loaded.packet_population
    loaded_packet = loaded.packet_population[packet.packet_id]
    assert loaded_packet.origin is not None
    assert loaded_packet.origin.unresolved_origin_residuals == ["origin-residual"]
    assert loaded_packet.boundary_refs is not None
    assert loaded_packet.boundary_refs.reachability_certificate_refs == ["reach"]
    assert loaded_packet.ecological_invariants.preserve_aperture is False
    assert loaded.residual_ledger.events[0].event_payload["post_residuals"]
    assert loaded.archive == {"raw": True}
    assert loaded.reusable_intelligence_capital == {"packet": "value"}


def test_model_serde_optional_and_error_branches() -> None:
    assert serde.optional_dict(None, name="x") is None
    assert serde.dict_value(None, name="x") == {}
    assert serde.string_list(None) == []
    assert serde.digest_from_json("abc") == Digest("sha256", "abc")
    digest = Digest("sha256", "abc")
    assert serde.digest_from_json(digest) is digest
    ref = serde.object_ref_from_json("object", bundle_id="bundle")
    assert ref.object_id == "object"
    assert serde.object_ref_from_json(ref) is ref

    assert serde.origin_from_json(None) is None
    assert serde.scope_from_json(None) is None
    assert serde.transformation_from_json(None) is None
    assert serde.procedure_from_json(None) is None
    assert serde.certification_condition_from_json(None) is None
    assert serde.boundary_refs_from_json(None) is None
    assert serde.residual_hooks_from_json(None) is None
    assert serde.update_profile_from_json(None) is None
    assert serde.circulation_status_from_json(None) is None
    assert serde.anti_overclosure_from_json(None).unknowns_to_preserve == []
    assert serde.ecological_invariants_from_json(None).preserve_origin is True
    assert serde.residual_liveness_from_json(None).owner == ""
    assert serde.residual_route_from_json(None) is None
    assert serde.history_from_json(["legacy"]).events == []
    assert serde.history_from_json({"events": "bad"}).events == []
    history = serde.history_from_json({"events": ["bad", {"payload": "not-dict"}]})
    assert history.events[0].payload == {}
    assert serde.ecology_state_from_json(["legacy"]).archive["json_store_snapshot"] == ["legacy"]
    sparse_state = serde.ecology_state_from_json(
        {
            "packet_population": [],
            "residual_ledger": [],
            "archive": [],
            "reusable_intelligence_capital": [],
        }
    )
    assert sparse_state.packet_population == {}
    dict_ledger = serde.ledger_from_json(
        {
            "residuals": {
                "r": {
                    "kind": "unresolved",
                    "origin": "o",
                    "scope": ["s"],
                    "obligation": "route",
                    "residual_id": "r",
                }
            },
            "events": [],
        }
    )
    assert "r" in dict_ledger.residuals

    with pytest.raises(ValueError, match="must be an object"):
        serde.as_dict([], name="bad")
    with pytest.raises(ValueError, match="expected a list"):
        serde.string_list("bad")
    with pytest.raises(ValueError, match="ledger residuals"):
        serde.ledger_from_json({"residuals": "bad"})
    with pytest.raises(ValueError, match="ledger events"):
        serde.ledger_from_json({"events": "bad"})


def test_model_serde_judgment_and_authority_variants() -> None:
    ref = {
        "bundle_id": "b",
        "object_id": "o",
        "schema_id": "schema",
        "digest": {"algorithm_id": "sha256", "value": "abc"},
    }
    judgment = serde.judgment_record_from_json(
        {
            "judgment_kind": "support",
            "subject": ref,
            "canonical_input_ref": ref,
            "canonical_digest": {"algorithm_id": "sha256", "value": "abc"},
            "input_digest": {"algorithm_id": "sha256", "value": "abc"},
            "JValid_result": "pass",
        },
        bundle_id="b",
    )
    assert isinstance(judgment, JudgmentRecord)
    assert serde.judgment_record_from_json(judgment) is judgment

    contract = serde.judgment_contract_from_json({"allowed_results": ["pass"]})
    assert contract.allowed_results == ("pass",)
    context = serde.use_context_from_json(
        {
            "subject_ref": ref,
            "canonical_input_ref": ref,
            "input_digest": {"algorithm_id": "sha256", "value": "abc"},
        },
        bundle_id="b",
    )
    assert context.subject_ref.object_id == "o"
    auth_inputs = serde.auth_inputs_from_json(
        {
            "auth_inputs_ref": "ai",
            "canonical_digest": {"algorithm_id": "sha256", "value": "abc"},
            "support_refs": [ref, "support-2"],
            "input_digest": {"algorithm_id": "sha256", "value": "def"},
        },
        bundle_id="b",
    )
    assert auth_inputs.support_refs == ("o", "support-2")
    assert auth_inputs.input_digest is not None


def test_model_serde_reachability_certificate_round_trip() -> None:
    deadline = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    gap = SoundGapResidual.create(
        certificate_ref="reach",
        gap_kind="model_gap",
        semantic_target="target",
        operational_claim="claim",
        route=ResidualRoute("owner", deadline, ("1h",), "daily"),
    )
    certificate = ReachabilityCertificate(
        certificate_id="reach",
        object_id="packet",
        schema_version="1.0",
        canonical_digest=Digest("sha256", "abc"),
        status=LifecycleStatus.ACTIVE,
        predicate="absence",
        certificate_contract="contract",
        carrier_id="carrier",
        carrier_acceptance_judgment_ref="carrier-ok",
        carrier_type="proof",
        concretization_id="concrete",
        checker_id="checker",
        checker_acceptance_judgment_ref="checker-ok",
        checker_result="pass",
        claim_kind="exclusion",
        coverage_statement="covered",
        cover_check_result="pass",
        empty_concretization_statement="empty",
        empty_check_result="pass",
        cex_channel=CounterexampleChannel(
            "cex",
            "packet",
            cex_closed_result="closed_within_window",
        ),
        soundness_target="absence",
        soundgap_residuals=(gap,),
        operational_claim_basis=("basis",),
        falsification_attempts=("attempt",),
        open_counterexample_residuals=("open",),
    )

    loaded = serde.reachability_certificate_from_json(certificate.to_dict())

    assert loaded.certificate_id == "reach"
    assert loaded.soundgap_residuals[0].certificate_ref == "reach"
    assert loaded.admissible_exclusion().passed
