from datetime import UTC, datetime, timedelta

from verification_ecology_kit import ResidualLedger, ResidualRecord
from verification_ecology_kit.model.records import ResidualKind
from verification_ecology_kit.model.residuals import ResidualRoute

deadline = (datetime.now(UTC) + timedelta(days=7)).isoformat()
residual = ResidualRecord(
    kind=ResidualKind.UNRESOLVED,
    origin="example",
    scope=("example",),
    obligation="inspect unresolved example",
    route=ResidualRoute("owner", deadline, ("1h",), "weekly"),
)

ledger = ResidualLedger()
ledger.add(residual, justification="example")
print(ledger.trace_ok().to_dict())
