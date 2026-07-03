from verification_ecology_kit import ObjectEnvelope
from verification_ecology_kit.digest import Digest
from verification_ecology_kit.references import SchemaMigrationWitness

source = ObjectEnvelope("packet-1", "verifier-packet", "1.0", {"status": "active"})
source_digest = source.refresh_digest()
source_ref = source.ref(bundle_id="migration-example")

witness = SchemaMigrationWitness(
    migration_witness_id="migration-1",
    from_schema_version="1.0",
    to_schema_version="1.1",
    field_mapping_ref=source_ref,
    transformed_object_ref=source_ref,
    source_digest=source_digest,
    target_digest=Digest("sha256", "changed"),
    loss_residual_refs=("residual-field-loss",),
    migration_judgment_ref="judgment-migration",
)

print(witness.to_dict())
print({"preserves_or_residualizes_loss": witness.preserves_or_residualizes_loss()})
