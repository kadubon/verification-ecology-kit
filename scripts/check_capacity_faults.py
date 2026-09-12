"""Bounded guard-removal fault injection in isolated disposable package copies."""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

from defusedxml import ElementTree

ROOT = Path(__file__).resolve().parents[1]
FAULTS = (
    ("reducer.py", "result exceeds reservation", "unit/test_capacity.py", "substitution"),
    ("reducer.py", "conflicting duplicate result", "unit/test_capacity.py", "attempt_accounting"),
    ("checker.py", "uncertified separation", "unit/test_capacity.py", "schedule_resources"),
    ("checker.py", "stale or substituted plan", "unit/test_capacity.py", "plan_read_only"),
    ("formal.py", "authority inflation", "formal/test_capacity_conformance.py", "actual_reducer"),
    (
        "formal.py",
        "work conservation failure",
        "formal/test_capacity_conformance.py",
        "actual_reducer",
    ),
)


class RemoveGuard(ast.NodeTransformer):
    def __init__(self, message: str):
        self.message = message
        self.changed = 0

    def visit_Call(self, node: ast.Call) -> ast.AST:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "require"
            and len(node.args) == 2
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == self.message
        ):
            node.args[0] = ast.Constant(value=True)
            self.changed += 1
        return self.generic_visit(node)


def main() -> int:
    outcomes = []
    for filename, guard, test, selection in FAULTS:
        with tempfile.TemporaryDirectory(prefix="vek-fault-") as tmp:
            target = Path(tmp)
            package = target / "verification_ecology_kit"
            shutil.copytree(
                ROOT / "src/verification_ecology_kit",
                package,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            path = package / "capacity" / filename
            tree = ast.parse(path.read_text(encoding="utf-8"))
            mutation = RemoveGuard(guard)
            tree = mutation.visit(tree)
            assert mutation.changed == 1, f"fault site drift: {guard}"
            path.write_text(ast.unparse(ast.fix_missing_locations(tree)), encoding="utf-8")
            junit = target / "result.xml"
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(target)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(ROOT / "tests" / test),
                    "-k",
                    selection,
                    "-o",
                    "addopts=",
                    "--no-cov",
                    f"--junitxml={junit}",
                    "-q",
                ],
                cwd=target,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )  # nosec B603
            summary = ElementTree.parse(junit).getroot().find("testsuite")
            assert summary is not None
            killed = (
                result.returncode == 1
                and int(summary.attrib["failures"]) > 0
                and int(summary.attrib["errors"]) == 0
            )
            outcomes.append(
                {
                    "file": filename,
                    "guard": guard,
                    "status": "killed" if killed else "incomplete-or-survived",
                    "tests": int(summary.attrib["tests"]),
                }
            )
    print(json.dumps(outcomes, indent=2))
    return 0 if all(row["status"] == "killed" for row in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
