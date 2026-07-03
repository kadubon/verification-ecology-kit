from verification_ecology_kit.digest import Digest
from verification_ecology_kit.model.reachability import (
    CounterexampleChannel,
    ReachabilityCertificate,
)
from verification_ecology_kit.model.records import LifecycleStatus

certificate = ReachabilityCertificate(
    certificate_id="reach-1",
    object_id="packet-1",
    schema_version="1.0",
    canonical_digest=Digest("sha256", "example"),
    status=LifecycleStatus.ACTIVE,
    predicate="destructive",
    certificate_contract="absence-v1",
    carrier_id="carrier-1",
    carrier_acceptance_judgment_ref="carrier-accepted",
    carrier_type="proof_object",
    concretization_id="concretization-1",
    checker_id="checker-1",
    checker_acceptance_judgment_ref="checker-accepted",
    checker_result="pass",
    claim_kind="exclusion",
    coverage_statement="covered by proof object",
    cover_check_result="pass",
    empty_concretization_statement="no destructive continuation found",
    empty_check_result="pass",
    cex_channel=CounterexampleChannel(
        channel_id="cex-1",
        target_ref="packet-1",
        cex_closed_result="closed_within_window",
    ),
    soundness_target="destructive reachability absence",
)

print(certificate.admissible_exclusion().to_dict())
