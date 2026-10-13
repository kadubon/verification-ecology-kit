# Workflow map

Use the least expansive command that matches the object.

| Need | Existing interface | Read next only if needed |
| --- | --- | --- |
| Environment and available schemas | `vek doctor`, `vek schema list` | `docs/cli.md` |
| Structure of one object | `vek validate OBJECT.json --schema SCHEMA --profile core` | schema documentation |
| Canonical identity | `vek digest OBJECT.json` | digest policy in `docs/conformance.md` |
| Bundle references | `vek refs check BUNDLE.json` | `docs/conformance.md` |
| Ordered support checks | `vek conformance BUNDLE.json --profile core --format json` | operational/federated profile rules |
| Ecology or independence risk | `vek audit packet-ecology ...` or `vek audit monoculture ...` | `docs/audits.md` |

Run audits against a provided file; do not invent an absent packet, authority record, or residual.
