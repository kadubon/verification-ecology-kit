"""Reproducible inert contracts and positive/negative capacity report fixtures."""

import json
from copy import deepcopy
from pathlib import Path

from verification_ecology_kit.capacity.examples import NAMES, scenario
from verification_ecology_kit.capacity.report import capacity_report
from verification_ecology_kit.capacity.runtime import CapacityRuntime
from verification_ecology_kit.runtime.in_memory import InMemoryStore


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "src/verification_ecology_kit/capacity/fixtures"
    for name in NAMES:
        contract, state = scenario(name)
        (root / f"{name}.json").write_text(
            json.dumps(contract.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        if name == "integrated":
            runtime = CapacityRuntime(InMemoryStore(state), contract)
            report = capacity_report(contract, runtime.inspect(), runtime.plan())
            (root / "report-positive.json").write_text(
                json.dumps(report, indent=2) + "\n", encoding="utf-8"
            )
            bad = deepcopy(report)
            bad["service_guaranteed_lower_envelope"] = "fabricated-average-guarantee"
            (root / "report-negative.json").write_text(
                json.dumps(bad, indent=2) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    main()
