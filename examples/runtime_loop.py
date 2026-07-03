from datetime import UTC, datetime, timedelta

from verification_ecology_kit.model.records import ResidualKind
from verification_ecology_kit.model.residuals import ResidualRecord, ResidualRoute
from verification_ecology_kit.runtime.engine import RuntimeEngine
from verification_ecology_kit.runtime.in_memory import InMemoryStore

store = InMemoryStore()
state = store.load()
deadline = (datetime.now(UTC) + timedelta(days=3)).isoformat()
state.residual_ledger.add(
    ResidualRecord(
        kind=ResidualKind.UNRESOLVED,
        origin="history",
        scope=("unknown",),
        obligation="generate candidate packet",
        route=ResidualRoute("owner", deadline, ("1h",), "next_runtime"),
    )
)

report = RuntimeEngine(store=store).run_once()
print(report.to_dict())
