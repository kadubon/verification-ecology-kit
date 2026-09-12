"""Offline installed-wheel regression scenarios; callable outside a source checkout."""

from __future__ import annotations

import contextlib
import io
import json
import socket
from importlib.metadata import version
from unittest.mock import patch

from verification_ecology_kit import __version__
from verification_ecology_kit.capacity.examples import NAMES, run_example, scenario
from verification_ecology_kit.capacity.interchange import cait_envelope, ccr_proposals
from verification_ecology_kit.capacity.report import capacity_report
from verification_ecology_kit.capacity.runtime import CapacityRuntime
from verification_ecology_kit.cli import main
from verification_ecology_kit.model.conformance import ConformanceEngine, VetBundle
from verification_ecology_kit.model.packets import VerifierPacket
from verification_ecology_kit.model.records import ConformanceProfile
from verification_ecology_kit.references import ObjectEnvelope, SchemaCatalogue
from verification_ecology_kit.runtime.in_memory import InMemoryStore


def run() -> dict[str, object]:
    """Block socket connects during every package operation in this process."""
    with (
        patch.object(socket.socket, "connect", side_effect=RuntimeError("offline smoke")),
        patch.object(socket, "create_connection", side_effect=RuntimeError("offline smoke")),
    ):
        assert version("verification-ecology-kit") == __version__
        with contextlib.redirect_stdout(io.StringIO()):
            assert main(["doctor"]) == 0
        packet = VerifierPacket.minimal()
        packet.ensure_core_accountability()
        packet.ensure_semantic_accountability()
        assert packet.validate()
        envelope = ObjectEnvelope("installed-object", "schema", "1.0", {"value": "fixture"})
        envelope.refresh_digest()
        bundle = VetBundle(
            "installed-smoke",
            "1",
            ConformanceProfile.CORE,
            SchemaCatalogue("installed-catalogue", {"schema": ("1.0",)}),
            objects=[envelope],
        )
        assert ConformanceEngine().run(bundle).decision.value == "accept"
        outcomes = {name: run_example(name)["snapshot"] for name in NAMES}
        c, state = scenario("integrated")
        runtime = CapacityRuntime(InMemoryStore(state), c)
        report = capacity_report(c, runtime.inspect(), runtime.plan())
        assert cait_envelope(report)["arrival_verdict"] is None
        assert len(ccr_proposals(c, revision="fixture-1", pool_ids=["pool", "budget"])) == 3
    return {
        "version": __version__,
        "offline": True,
        "scenarios": sorted(outcomes),
        "doctor": "passed",
        "conformance": "executed",
        "interchange": "passed",
    }


if __name__ == "__main__":
    import sys

    sys.stdout.write(json.dumps(run(), indent=2) + "\n")
