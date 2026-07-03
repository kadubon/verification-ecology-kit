# Theory Mapping

| Theory term | Module | JSON schema | Tests | Docs |
| --- | --- | --- | --- | --- |
| ObservableProcessHistory | model/history.py | vet-bundle.schema.json | tests/unit/test_history_ledger.py | docs/data_model.md |
| VerifierPacket | model/packets.py | verifier-packet.schema.json | tests/unit/test_packets_operations.py | docs/concepts.md |
| ResidualLedger | model/ledger.py | residual-ledger.schema.json | tests/unit/test_history_ledger.py | docs/data_model.md |
| ConformanceAlgorithm | model/conformance.py | conformance-report.schema.json | tests/unit/test_conformance_authority.py | docs/conformance.md |
| AuthorityDecision | model/authority.py | authority-decision.schema.json | tests/unit/test_conformance_authority.py | docs/conformance.md |
| OverclosureWitness | model/overclosure.py | residual-record.schema.json | tests/unit/test_audits_runtime.py | docs/audits.md |