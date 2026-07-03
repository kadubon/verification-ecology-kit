from __future__ import annotations

from pathlib import Path

from verification_ecology_kit.audit.reports import AuditReport
from verification_ecology_kit.audit.security import verify_package_archives


def verify_dist(dist: Path = Path("dist")) -> AuditReport:
    return verify_package_archives(dist)


def main() -> int:
    report = verify_dist()
    print(report.to_json())
    return 0 if report.decision == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
