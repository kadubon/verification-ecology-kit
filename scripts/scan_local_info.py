from __future__ import annotations

import argparse
import sys
from pathlib import Path

from verification_ecology_kit.audit.local_info import scan_local_info


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--allowlist", type=Path, default=None)
    args = parser.parse_args(sys.argv[1:])
    report = scan_local_info(Path(args.path), allowlist_path=args.allowlist)
    print(report.to_json())
    return 0 if report.decision == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
