from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

from verification_ecology_kit.audit.security import verify_package_paths


def main() -> int:
    dist = Path("dist")
    paths: list[Path] = []
    if dist.exists():
        for archive in dist.iterdir():
            if archive.suffix == ".whl":
                with zipfile.ZipFile(archive) as wheel:
                    paths.extend(Path(name) for name in wheel.namelist())
            elif archive.suffixes[-2:] == [".tar", ".gz"]:
                with tarfile.open(archive) as sdist:
                    paths.extend(Path(member.name) for member in sdist.getmembers())
    report = verify_package_paths(paths)
    print(report.to_json())
    return 0 if report.decision == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
