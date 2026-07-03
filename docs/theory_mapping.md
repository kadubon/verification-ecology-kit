# Theory Mapping

This page maps Verifier Ecology Theory terms to the package artifacts that
implement their operational checks. The fuller v1 audit matrix is in
[V1 Audit](v1_audit.md).

| Theory term | Plain wording | Module | JSON schema | Tests | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ObservableProcessHistory | observable process history | model/history.py | vet-bundle.schema.json | tests/unit/test_history_ledger.py, tests/property/test_properties.py | docs/data_model.md | implemented |
| VerifierEcologyState | verifier ecology state | model/ecology_state.py | runtime-report.schema.json | tests/unit/test_audits_runtime.py, tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| TypeEnvironment | type environment | model/records.py | schema-catalogue.schema.json | tests/unit/test_records_lifecycle.py | docs/data_model.md | implemented |
| TypedPartialRecord | typed partial record | model/records.py | schema-catalogue.schema.json | tests/unit/test_records_lifecycle.py | docs/data_model.md | implemented |
| ObservationSignature | observation signature | model/records.py | schema-catalogue.schema.json | tests/unit/test_records_lifecycle.py | docs/data_model.md | implemented |
| ObjectEnvelope | object envelope | references.py | vet-object-envelope.schema.json | tests/unit/test_canonical_digest_refs.py | docs/data_model.md | implemented |
| ObjectRef | object reference | references.py | vet-object-ref.schema.json | tests/unit/test_canonical_digest_refs.py | docs/data_model.md | implemented |
| ReferenceEdge | reference edge | references.py | reference-edge.schema.json | tests/unit/test_canonical_digest_refs.py | docs/data_model.md | implemented |
| DigestRecord | digest record | references.py | digest-record.schema.json | tests/unit/test_golden_fixtures.py | docs/data_model.md | implemented |
| SchemaCatalogue | schema catalogue | references.py | schema-catalogue.schema.json | tests/unit/test_canonical_digest_refs.py, tests/unit/test_cli_json_loaders.py | docs/schemas.md | implemented |
| SchemaMigrationWitness | schema migration witness | references.py | schema-migration-witness.schema.json | tests/unit/test_golden_fixtures.py | docs/schemas.md | implemented |
| CarrierRegistry | carrier registry | model/registries.py | carrier-registry.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| CheckerRegistry | checker registry | model/registries.py | checker-registry.schema.json | tests/unit/test_golden_fixtures.py | docs/data_model.md | implemented |
| ContractRegistry | contract registry | model/contracts.py | contract-registry.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| JudgmentContract | judgment contract | model/contracts.py | contract-registry.schema.json | tests/unit/test_extended_models.py | docs/conformance.md | implemented |
| CarrierContract | carrier contract | model/contracts.py | contract-registry.schema.json | tests/unit/test_extended_models.py | docs/conformance.md | implemented |
| CheckerContract | checker contract | model/contracts.py | contract-registry.schema.json | tests/unit/test_extended_models.py | docs/conformance.md | implemented |
| UseContext | use context | model/judgments.py | use-context.schema.json | tests/unit/test_branch_coverage.py | docs/conformance.md | implemented |
| JudgmentRecord | judgment record | model/judgments.py | judgment-record.schema.json | tests/unit/test_branch_coverage.py, tests/unit/test_conformance_authority.py | docs/conformance.md | implemented |
| JValid | j valid | model/judgments.py | judgment-record.schema.json | tests/unit/test_branch_coverage.py | docs/conformance.md | implemented |
| Lifecycle StatusEvent / StatusStep / StatusView / StatusFold | lifecycle status event status step status view status fold | model/lifecycle.py | lifecycle-status-event.schema.json, status-view.schema.json | tests/unit/test_records_lifecycle.py | docs/conformance.md | implemented |
| ResidualRecord | residual record | model/residuals.py | residual-record.schema.json | tests/unit/test_history_ledger.py | docs/data_model.md | implemented |
| Residual route and liveness / ResidualRoute | residual route and liveness residual route | model/residuals.py | residual-record.schema.json | tests/unit/test_history_ledger.py | docs/data_model.md | implemented |
| ResidualLedger | residual ledger | model/ledger.py | residual-ledger.schema.json | tests/unit/test_history_ledger.py, tests/property/test_properties.py | docs/data_model.md | implemented |
| Residual metabolism | residual metabolism | audit/residual_metabolism.py | audit-report.schema.json | tests/unit/test_audits_runtime.py | docs/audits.md | implemented |
| LedgerEvent | ledger event | model/ledger.py | ledger-event.schema.json | tests/unit/test_history_ledger.py | docs/data_model.md | implemented |
| TraceCertificate | trace certificate | model/ledger.py | residual-ledger.schema.json | tests/unit/test_golden_fixtures.py | docs/data_model.md | implemented |
| TraceOK | trace o k | model/ledger.py | residual-ledger.schema.json | tests/unit/test_history_ledger.py, tests/property/test_properties.py | docs/data_model.md | implemented |
| VerifierPacket | verifier packet | model/packets.py | verifier-packet.schema.json | tests/unit/test_packets_operations.py, tests/integration/test_cli_extended.py | docs/concepts.md | implemented |
| CoreAccountablePacket | core accountable packet | model/packets.py | verifier-packet.schema.json | tests/unit/test_packets_operations.py | docs/concepts.md | implemented |
| CounterPacket | counter packet | model/packets.py | verifier-packet.schema.json | tests/unit/test_golden_fixtures.py | docs/audits.md | implemented |
| BoundaryTesterPacket | boundary tester packet | model/packets.py | verifier-packet.schema.json | tests/unit/test_golden_fixtures.py | docs/audits.md | implemented |
| BoundaryRecord | boundary record | model/boundaries.py | boundary-record.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| ContinuationSpecification | continuation specification | model/reachability.py | continuation-specification.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| ReachabilityCertificate | reachability certificate | model/reachability.py | reachability-certificate.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| CounterexampleChannel | counterexample channel | model/reachability.py | counterexample-channel.schema.json | tests/unit/test_branch_coverage.py | docs/data_model.md | implemented |
| Soundness-gap residual / SoundGapResidual | soundness gap residual sound gap residual | model/residuals.py | sound-gap-residual.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| CertificationRecord | certification record | model/certification.py | certification-record.schema.json | tests/unit/test_conformance_authority.py | docs/data_model.md | implemented |
| CertificationProfile | certification profile | model/certification.py | certification-profile.schema.json | tests/unit/test_conformance_authority.py | docs/data_model.md | implemented |
| Certification promotion criterion | certification promotion criterion | model/certification.py | certification-record.schema.json | tests/unit/test_conformance_authority.py | docs/conformance.md | implemented |
| AuthorityDecision | authority decision | model/authority.py | authority-decision.schema.json | tests/unit/test_conformance_authority.py | docs/conformance.md | implemented |
| AuthInputs | auth inputs | model/authority.py | auth-inputs.schema.json | tests/unit/test_extended_models.py | docs/conformance.md | implemented |
| Authority aggregation | authority aggregation | model/authority.py | authority-decision.schema.json | tests/unit/test_conformance_authority.py, tests/property/test_properties.py | docs/conformance.md | implemented |
| Aperture | aperture | model/aperture.py | aperture.schema.json | tests/unit/test_audits_runtime.py | docs/audits.md | implemented |
| CapacityRecord | capacity record | model/aperture.py | aperture.schema.json | tests/unit/test_audits_runtime.py | docs/audits.md | implemented |
| VerifiableFrontierProfile | verifiable frontier profile | model/frontier.py | frontier-profile.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| OverclosureWitness | overclosure witness | model/overclosure.py | overclosure-witness.schema.json | tests/unit/test_golden_fixtures.py | docs/audits.md | implemented |
| SchemaOverclosureDetector | schema overclosure | model/overclosure.py | audit-report.schema.json | tests/unit/test_audits_runtime.py, tests/integration/test_cli.py | docs/audits.md | implemented |
| VerifierMonocultureDetector | monoculture | model/overclosure.py | audit-report.schema.json | tests/unit/test_audits_runtime.py, tests/integration/test_cli_extended.py | docs/audits.md | implemented |
| ExternalPacket | external packet | model/circulation.py | verifier-packet.schema.json | tests/unit/test_extended_models.py | docs/concepts.md | implemented |
| LocalInternalization pipeline | local internalization pipeline | model/circulation.py | verifier-packet.schema.json | tests/unit/test_extended_models.py, tests/integration/test_cli_extended.py | docs/concepts.md | implemented |
| LocalSovereignty | local sovereignty | model/circulation.py | verifier-packet.schema.json | tests/unit/test_extended_models.py | docs/concepts.md | implemented |
| MaturityProfile | maturity profile | model/maturity.py | maturity-profile.schema.json | tests/unit/test_extended_models.py | docs/data_model.md | implemented |
| VetBundle | bundle | model/conformance.py | vet-bundle.schema.json | tests/unit/test_conformance_authority.py, tests/integration/test_cli_extended.py | docs/conformance.md | implemented |
| ConformanceProfile | conformance profile | model/records.py | conformance-report.schema.json | tests/unit/test_conformance_authority.py | docs/conformance.md | implemented |
| ConformanceEngine | conformance engine | model/conformance.py | conformance-report.schema.json | tests/unit/test_conformance_authority.py, tests/integration/test_cli_extended.py | docs/conformance.md | implemented |
| RuntimeEngine | runtime engine | runtime/engine.py | runtime-report.schema.json | tests/unit/test_audits_runtime.py, tests/unit/test_extended_models.py | docs/examples.md | implemented |
| AuditEngine | audit engine | audit/reports.py | audit-report.schema.json | tests/unit/test_audits_runtime.py | docs/audits.md | implemented |
| secret/local-info/package-content scanners | secret local info package content scanners | audit/security.py, audit/local_info.py, scripts/verify_package_contents.py | audit-report.schema.json | tests/security/test_scanners.py | docs/security.md | implemented |
