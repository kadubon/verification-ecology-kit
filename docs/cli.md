# CLI

`vek` commands:

- `vek init`
- `vek schema list`
- `vek schema export --out DIR`
- `vek validate OBJECT.json --schema SCHEMA --profile core`
- `vek conformance BUNDLE.json --profile core --format json`
- `vek digest OBJECT.json`
- `vek refs check BUNDLE.json`
- `vek ledger replay LEDGER.json`
- `vek packet create --template minimal`
- `vek packet operate fork PACKET.json --out forked-packet.json`
- `vek packet operate specialize PACKET.json --scope SCOPE --out scoped-packet.json`
- `vek packet operate compose LEFT.json RIGHT.json --out composed-packet.json`
- `vek packet operate contrast LEFT.json RIGHT.json --out contrast-packet.json`
- `vek packet operate repair PACKET.json --repair-note NOTE --out repaired-packet.json`
- `vek packet operate retire PACKET.json --reason REASON --out retired-packet.json`
- `vek packet operate quarantine PACKET.json --reason REASON --out quarantined-packet.json`
- `vek packet operate internalize PACKET.json --translated true --boundary-checked true --out local-packet.json`
- `vek packet operate redact PACKET.json --field FIELD --out redacted-packet.json`
- `vek audit packet-ecology PACKET_OR_BUNDLE.json`
- `vek audit residual-metabolism STATE_OR_LEDGER.json`
- `vek audit aperture-regression BEFORE.json AFTER.json`
- `vek audit adversarial-ingress PACKET.json`
- `vek audit schema-overclosure SCHEMA_AUDIT.json`
- `vek audit monoculture PACKETS_OR_BUNDLE.json`
- `vek runtime run CONFIG.json`
- `vek scan leaks PATH`
- `vek scan local-info PATH`
- `vek doctor`
- `vek version`

`packet operate` always reads one or more packet JSON files and writes the new
packet to `--out`. The JSON report printed to stdout includes the operation
name, input packet ids, output packet, check results, residual refs, and output
path.

Audits always read an input file. Packet audits accept a single packet, a list
of packets, a state with `packet_population`, or a bundle whose objects include
`schema_id: "verifier-packet"`.
