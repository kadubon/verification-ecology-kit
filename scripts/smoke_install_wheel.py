from __future__ import annotations

import shutil
import subprocess  # nosec B404
import sys
import tomllib
from pathlib import Path


def main() -> int:
    version = _project_version()
    wheels = sorted(Path("dist").glob(f"verification_ecology_kit-{version}-*.whl"))
    if len(wheels) != 1:
        print(f"expected exactly one wheel for {version}, found {len(wheels)}", file=sys.stderr)
        return 1
    uv = shutil.which("uv")
    if uv is None:
        print("uv executable not found", file=sys.stderr)
        return 1
    command = [
        uv,
        "run",
        "--with",
        str(wheels[0]),
        "--no-project",
        "--",
        "python",
        "-c",
        (
            "import verification_ecology_kit; "
            f"assert verification_ecology_kit.__version__ == {version!r}; "
            "print(verification_ecology_kit.__version__)"
        ),
    ]
    completed = subprocess.run(command, check=False)  # nosec B603
    return completed.returncode


def _project_version() -> str:
    with Path("pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])


if __name__ == "__main__":
    raise SystemExit(main())
