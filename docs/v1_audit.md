# V1 Audit

This audit maps the theory-facing terms from Verifier Ecology Theory to the
software artifacts that make them operational in this package. The package does
not claim to prove the paper's theorems. It implements deterministic records,
schema contracts, checks, audits, reports, and residual obligations that can be
run by users and CI.

The machine-readable witness for this page is
`tests/golden/theory_coverage.expected.json`.

## Coverage Matrix

| Theory term | Module and public API | Schema | CLI coverage | Tests | Docs | Status / residual |
| --- | --- | --- | --- | --- | --- | --- |
| ObservableProcessHistory | `model/history.py`: `ObservableProcessHistory` | `vet-bundle.schema.json` | `vek runtime run` | `tests/unit/test_history_ledger.py`, `tests/property/test_properties.py` | `docs/data_model.md` | implemented |
| VerifierEcologyState | `model/ecology_state.py`: `VerifierEcologyState` | `runtime-report.schema.json` | `vek runtime run` | `tests/unit/test_audits_runtime.py`, `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| TypeEnvironment | `model/records.py`: `TypeEnvironment` | `schema-catalogue.schema.json` | `vek conformance` through bundle metadata | `tests/unit/test_records_lifecycle.py` | `docs/data_model.md` | implemented |
| TypedPartialRecord | `model/records.py`: `TypedPartialRecord` | `schema-catalogue.schema.json` | `vek validate` for schema-bound records | `tests/unit/test_records_lifecycle.py` | `docs/data_model.md` | implemented |
| ObservationSignature | `model/records.py`: `ObservationSignature` | `schema-catalogue.schema.json` | `vek conformance` through bundle metadata | `tests/unit/test_records_lifecycle.py` | `docs/data_model.md` | implemented |
| ObjectEnvelope | `references.py`: `ObjectEnvelope` | `vet-object-envelope.schema.json` | `vek conformance`, `vek refs check` | `tests/unit/test_canonical_digest_refs.py` | `docs/data_model.md` | implemented |
| ObjectRef | `references.py`: `ObjectRef` | `vet-object-ref.schema.json` | `vek refs check` | `tests/unit/test_canonical_digest_refs.py` | `docs/data_model.md` | implemented |
| ReferenceEdge | `references.py`: `ReferenceEdge` | `reference-edge.schema.json` | `vek refs check` | `tests/unit/test_canonical_digest_refs.py` | `docs/data_model.md` | implemented |
| DigestRecord | `references.py`: `DigestRecord` | `digest-record.schema.json` | `vek digest` | `tests/unit/test_golden_fixtures.py` | `docs/data_model.md` | implemented |
| SchemaCatalogue | `references.py`: `SchemaCatalogue` | `schema-catalogue.schema.json` | `vek schema list`, `vek schema export`, `vek conformance` | `tests/unit/test_canonical_digest_refs.py`, `tests/unit/test_cli_json_loaders.py` | `docs/schemas.md` | implemented |
| SchemaMigrationWitness | `references.py`: `SchemaMigrationWitness` | `schema-migration-witness.schema.json` | `vek conformance` through bundle metadata | `tests/unit/test_golden_fixtures.py` | `docs/schemas.md` | implemented |
| CarrierRegistry | `model/registries.py`: `CarrierRegistry` | `carrier-registry.schema.json` | `vek conformance` through operational evidence | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| CheckerRegistry | `model/registries.py`: `CheckerRegistry` | `checker-registry.schema.json` | `vek conformance` through operational evidence | `tests/unit/test_golden_fixtures.py` | `docs/data_model.md` | implemented |
| ContractRegistry | `model/contracts.py`: `ContractRegistry` | `contract-registry.schema.json` | `vek conformance` through operational evidence | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| JudgmentContract | `model/contracts.py`: `JudgmentContract` | `contract-registry.schema.json` | `vek conformance` | `tests/unit/test_extended_models.py` | `docs/conformance.md` | implemented |
| CarrierContract | `model/contracts.py`: `CarrierContract` | `contract-registry.schema.json` | `vek conformance` | `tests/unit/test_extended_models.py` | `docs/conformance.md` | implemented |
| CheckerContract | `model/contracts.py`: `CheckerContract` | `contract-registry.schema.json` | `vek conformance` | `tests/unit/test_extended_models.py` | `docs/conformance.md` | implemented |
| UseContext | `model/judgments.py`: `UseContext` | `use-context.schema.json` | `vek conformance` through judgment records | `tests/unit/test_branch_coverage.py` | `docs/conformance.md` | implemented |
| JudgmentRecord | `model/judgments.py`: `JudgmentRecord` | `judgment-record.schema.json` | `vek conformance` | `tests/unit/test_branch_coverage.py`, `tests/unit/test_conformance_authority.py` | `docs/conformance.md` | implemented |
| JValid | `model/judgments.py`: `jvalid` | `judgment-record.schema.json` | `vek conformance` | `tests/unit/test_branch_coverage.py` | `docs/conformance.md` | implemented |
| Lifecycle StatusEvent / StatusStep / StatusView / StatusFold | `model/lifecycle.py`: `StatusEvent`, `StatusView`, `StatusFold` | `lifecycle-status-event.schema.json`, `status-view.schema.json` | `vek conformance` | `tests/unit/test_records_lifecycle.py` | `docs/conformance.md` | implemented |
| ResidualRecord | `model/residuals.py`: `ResidualRecord` | `residual-record.schema.json` | `vek ledger replay`, audits | `tests/unit/test_history_ledger.py` | `docs/data_model.md` | implemented |
| Residual route and liveness / ResidualRoute | `model/residuals.py`: `ResidualRoute` | `residual-record.schema.json` | `vek audit residual-metabolism` | `tests/unit/test_history_ledger.py` | `docs/data_model.md` | implemented |
| ResidualLedger | `model/ledger.py`: `ResidualLedger` | `residual-ledger.schema.json` | `vek ledger replay` | `tests/unit/test_history_ledger.py`, `tests/property/test_properties.py` | `docs/data_model.md` | implemented |
| Residual metabolism | `audit/residual_metabolism.py`: `audit_residual_metabolism` | `audit-report.schema.json` | `vek audit residual-metabolism` | `tests/unit/test_audits_runtime.py` | `docs/audits.md` | implemented |
| LedgerEvent | `model/ledger.py`: `LedgerEvent` | `ledger-event.schema.json` | `vek ledger replay` | `tests/unit/test_history_ledger.py` | `docs/data_model.md` | implemented |
| TraceCertificate | `model/ledger.py`: `TraceCertificate` | `residual-ledger.schema.json` | `vek ledger replay` | `tests/unit/test_golden_fixtures.py` | `docs/data_model.md` | implemented |
| TraceOK | `model/ledger.py`: `ResidualLedger.trace_ok` | `residual-ledger.schema.json` | `vek ledger replay` | `tests/unit/test_history_ledger.py`, `tests/property/test_properties.py` | `docs/data_model.md` | implemented |
| VerifierPacket | `model/packets.py`: `VerifierPacket` | `verifier-packet.schema.json` | `vek packet create`, `vek packet operate`, `vek audit packet-ecology` | `tests/unit/test_packets_operations.py`, `tests/integration/test_cli_extended.py` | `docs/concepts.md` | implemented |
| CoreAccountablePacket | `model/packets.py`: `CoreAccountablePacket` | `verifier-packet.schema.json` | `vek audit packet-ecology` | `tests/unit/test_packets_operations.py` | `docs/concepts.md` | implemented |
| CounterPacket | `model/packets.py`: `CounterPacket` | `verifier-packet.schema.json` | `vek audit packet-ecology`, `vek audit monoculture` | `tests/unit/test_golden_fixtures.py` | `docs/audits.md` | implemented |
| BoundaryTesterPacket | `model/packets.py`: `BoundaryTesterPacket` | `verifier-packet.schema.json` | `vek audit packet-ecology` | `tests/unit/test_golden_fixtures.py` | `docs/audits.md` | implemented |
| BoundaryRecord | `model/boundaries.py`: `BoundaryRecord` | `boundary-record.schema.json` | `vek audit aperture-regression`, packet audits through refs | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| ContinuationSpecification | `model/reachability.py`: `ContinuationSpecification` | `continuation-specification.schema.json` | `vek conformance` through operational bundle evidence | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| ReachabilityCertificate | `model/reachability.py`: `ReachabilityCertificate` | `reachability-certificate.schema.json` | `vek conformance` through operational bundle evidence | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| CounterexampleChannel | `model/reachability.py`: `CounterexampleChannel` | `counterexample-channel.schema.json` | `vek conformance` through certificate evidence | `tests/unit/test_branch_coverage.py` | `docs/data_model.md` | implemented |
| Soundness-gap residual / SoundGapResidual | `model/residuals.py`: `SoundGapResidual` | `sound-gap-residual.schema.json` | `vek audit residual-metabolism` | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| CertificationRecord | `model/certification.py`: `CertificationRecord` | `certification-record.schema.json` | `vek conformance` through operational bundle evidence | `tests/unit/test_conformance_authority.py` | `docs/data_model.md` | implemented |
| CertificationProfile | `model/certification.py`: `CertificationProfile` | `certification-profile.schema.json` | `vek conformance` through operational bundle evidence | `tests/unit/test_conformance_authority.py` | `docs/data_model.md` | implemented |
| Certification promotion criterion | `model/certification.py`: `CertificationEngine.promotion_check` | `certification-record.schema.json` | `vek conformance` through authority/certification records | `tests/unit/test_conformance_authority.py` | `docs/conformance.md` | implemented |
| AuthorityDecision | `model/authority.py`: `AuthorityDecision` | `authority-decision.schema.json` | `vek conformance` | `tests/unit/test_conformance_authority.py` | `docs/conformance.md` | implemented |
| AuthInputs | `model/authority.py`: `AuthInputs` | `auth-inputs.schema.json` | `vek conformance` | `tests/unit/test_extended_models.py` | `docs/conformance.md` | implemented |
| Authority aggregation | `model/authority.py`: `AuthorityEngine.aggregate` | `authority-decision.schema.json` | `vek conformance` | `tests/unit/test_conformance_authority.py`, `tests/property/test_properties.py` | `docs/conformance.md` | implemented |
| Aperture | `model/aperture.py`: `Aperture` | `aperture.schema.json` | `vek audit aperture-regression` | `tests/unit/test_audits_runtime.py` | `docs/audits.md` | implemented |
| CapacityRecord | `model/aperture.py`: `CapacityRecord` | `aperture.schema.json` | `vek audit aperture-regression` | `tests/unit/test_audits_runtime.py` | `docs/audits.md` | implemented |
| VerifiableFrontierProfile | `model/frontier.py`: `VerifiableFrontierProfile` | `frontier-profile.schema.json` | `vek runtime run` via runtime state | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| OverclosureWitness | `model/overclosure.py`: `OverclosureWitness` | `overclosure-witness.schema.json` | `vek audit schema-overclosure`, `vek audit monoculture` | `tests/unit/test_golden_fixtures.py` | `docs/audits.md` | implemented |
| SchemaOverclosureDetector | `model/overclosure.py`: `SchemaOverclosureDetector` | `audit-report.schema.json` | `vek audit schema-overclosure` | `tests/unit/test_audits_runtime.py`, `tests/integration/test_cli.py` | `docs/audits.md` | implemented |
| VerifierMonocultureDetector | `model/overclosure.py`: `VerifierMonocultureDetector` | `audit-report.schema.json` | `vek audit monoculture` | `tests/unit/test_audits_runtime.py`, `tests/integration/test_cli_extended.py` | `docs/audits.md` | implemented |
| ExternalPacket | `model/circulation.py`: `ExternalPacket` | `verifier-packet.schema.json` | `vek packet operate internalize` | `tests/unit/test_extended_models.py` | `docs/concepts.md` | implemented |
| LocalInternalization pipeline | `model/circulation.py`: `LocalSovereignty.internalize` | `verifier-packet.schema.json` | `vek packet operate internalize` | `tests/unit/test_extended_models.py`, `tests/integration/test_cli_extended.py` | `docs/concepts.md` | implemented |
| LocalSovereignty | `model/circulation.py`: `LocalSovereignty` | `verifier-packet.schema.json` | `vek packet operate internalize`, `vek audit adversarial-ingress` | `tests/unit/test_extended_models.py` | `docs/concepts.md` | implemented |
| MaturityProfile | `model/maturity.py`: `MaturityProfile` | `maturity-profile.schema.json` | `vek conformance` through operational evidence | `tests/unit/test_extended_models.py` | `docs/data_model.md` | implemented |
| VetBundle | `model/conformance.py`: `VetBundle` | `vet-bundle.schema.json` | `vek conformance`, `vek refs check` | `tests/unit/test_conformance_authority.py`, `tests/integration/test_cli_extended.py` | `docs/conformance.md` | implemented |
| ConformanceProfile | `model/records.py`: `ConformanceProfile` | `conformance-report.schema.json` | `vek conformance --profile` | `tests/unit/test_conformance_authority.py` | `docs/conformance.md` | implemented |
| ConformanceEngine | `model/conformance.py`: `ConformanceEngine` | `conformance-report.schema.json` | `vek conformance` | `tests/unit/test_conformance_authority.py`, `tests/integration/test_cli_extended.py` | `docs/conformance.md` | implemented |
| RuntimeEngine | `runtime/engine.py`: `RuntimeEngine` | `runtime-report.schema.json` | `vek runtime run` | `tests/unit/test_audits_runtime.py`, `tests/unit/test_extended_models.py` | `docs/examples.md` | implemented |
| AuditEngine | `audit/reports.py`: `AuditEngine` | `audit-report.schema.json` | `vek audit ...` | `tests/unit/test_audits_runtime.py` | `docs/audits.md` | implemented |
| secret/local-info/package-content scanners | `audit/security.py`, `audit/local_info.py`, `scripts/verify_package_contents.py` | `audit-report.schema.json` | `vek scan leaks`, `vek scan local-info` | `tests/security/test_scanners.py` | `docs/security.md` | implemented |

## Audit Result

All rows required for the v1 operational contract are implemented. Any future
extension that adds a theory term, public schema, or CLI workflow must update
this page and `tests/golden/theory_coverage.expected.json` in the same change.
