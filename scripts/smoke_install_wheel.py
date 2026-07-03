from __future__ import annotations

import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path


def main() -> int:
    wheels = sorted(Path("dist").glob("verification_ecology_kit-*.whl"))
    if len(wheels) != 1:
        print(f"expected exactly one wheel, found {len(wheels)}", file=sys.stderr)
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
        "import verification_ecology_kit; print(verification_ecology_kit.__version__)",
    ]
    completed = subprocess.run(command, check=False)  # nosec B603
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
