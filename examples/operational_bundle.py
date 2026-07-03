from verification_ecology_kit import ConformanceEngine, ObjectEnvelope
from verification_ecology_kit.model.conformance import VetBundle
from verification_ecology_kit.model.records import ConformanceProfile
from verification_ecology_kit.references import SchemaCatalogue

envelope = ObjectEnvelope("packet-1", "verifier-packet", "1.0", payload={})
envelope.refresh_digest()
bundle = VetBundle(
    bundle_id="example",
    schema_version="1.0",
    conformance_profile=ConformanceProfile.CORE,
    schema_catalogue=SchemaCatalogue("example", {"verifier-packet": ("1.0",)}),
    objects=[envelope],
)

print(ConformanceEngine().run(bundle).to_dict())
