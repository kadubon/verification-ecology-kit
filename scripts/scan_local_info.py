from __future__ import annotations

import sys
from pathlib import Path

from verification_ecology_kit.audit.local_info import scan_local_info


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    report = scan_local_info(path)
    print(report.to_json())
    return 0 if report.decision == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
