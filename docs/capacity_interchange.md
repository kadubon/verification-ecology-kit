# Capacity interchange and migration

The VEK-owned closed report identity is `vek_verification_capacity_report_v1`.
The packaged `capacity-report.schema.json` includes producer/schema versions,
contract/source digests, revision, units/horizon, model assumptions, local accounting,
resource pools/budgets, registered checks, branch forecasts, completeness and non-claims.
Report validation does not authenticate its producer. Observed service and guaranteed
service-envelope fields are null in this local synthetic/model profile.

The optional CCR adapter validates task proposals against the actual packaged
`ccr.task.v0.1` schema pinned from CCR commit
`6d8a30820806044b3a4b18d499fbe89bef83fbf2`, path `schemas/task.schema.json`.
The upstream source is https://github.com/kadubon/collective-capability-runtime.
`x_vek_capacity` carries original work bindings, separation requirements, typed cost
bounds, deadline slot, CCR revision and pool IDs. Extensions are proposals, not a claim
that CCR's base schema enforces these extensions. Unknown versions fail closed.
CCR owns leases, approval, atomic reservations, execution and reward. VEK does not
access CCR storage, issue approvals or impose an unconditional package dependency.

```text
vek capacity export contract.json --store ecology.json --format ccr --ccr-revision REV --ccr-pool POOL --ccr-pool BUDGET
vek capacity export contract.json --store ecology.json --format cait
```

CAIT schemas were inspected at commit `8ef4bc1ea272751804655a6e056467837ff35670`
of https://github.com/kadubon/cait-certificate-schema. They do not define this capacity
report. The CAIT-facing output is an explicitly partial VEK-owned JSON envelope,
readable without importing VEK, not CAIT certificate/arrival conformance. Arrival
verdict is null; growth-window accounting and endogenous attribution belong to CAIT.

Existing schema IDs, hashes, stored records, command defaults and public numeric
contracts are unchanged. Select this profile explicitly and register a finite contract
against current residuals. Do not migrate by dropping history or relabeling synthetic
results as observed records. No companion repository was modified for this adapter.
