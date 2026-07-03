from verification_ecology_kit import ConformanceEngine, ObjectEnvelope
from verification_ecology_kit.model.conformance import VetBundle
from verification_ecology_kit.model.records import ConformanceProfile
from verification_ecology_kit.references import SchemaCatalogue

packet = {
    "status": "active",
    "federated": {"local_sovereignty": True, "external_authority": False},
}
envelope = ObjectEnvelope("federated-packet", "verifier-packet", "1.0", payload=packet)
envelope.refresh_digest()

bundle = VetBundle(
    bundle_id="federated-example",
    schema_version="1.0",
    conformance_profile=ConformanceProfile.FEDERATED,
    schema_catalogue=SchemaCatalogue("example", {"verifier-packet": ("1.0",)}),
    objects=[envelope],
    authority_decisions=[
        {
            "authority_decision_id": "auth-local-use",
            "decision": "allow",
            "deny_by_default": True,
            "lifecycle_status": "active",
            "required_support_refs": ["support-local"],
            "support_judgment_refs": ["judgment-local"],
        }
    ],
    judgment_records=[{"judgment_id": "judgment-local", "jvalid_result": "pass"}],
)

print(ConformanceEngine().run(bundle).to_dict())
