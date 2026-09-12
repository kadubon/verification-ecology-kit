"""Install built wheel in a fresh environment and execute offline outside the checkout."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
import tempfile
import tomllib
from pathlib import Path


def main() -> int:
    with Path("pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]
    wheels = sorted(Path("dist").glob(f"verification_ecology_kit-{version}-*.whl"))
    if len(wheels) != 1:
        raise ValueError("expected exactly one wheel for current package version")
    uv = shutil.which("uv")
    if uv is None:
        raise ValueError("uv not found")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    with tempfile.TemporaryDirectory(prefix="vek-wheel-") as tmp:
        root = Path(tmp)
        subprocess.run([uv, "venv", str(root / "env"), "--seed"], check=True, env=env)  # nosec B603
        python = root / "env" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-cache-dir",
                "--index-url",
                "https://pypi.org/simple",
                str(wheels[0].resolve()),
            ],
            cwd=root,
            env=env,
            check=True,
        )  # nosec B603
        subprocess.run([str(python), "-m", "pip", "check"], cwd=root, env=env, check=True)  # nosec B603
        subprocess.run(
            [str(python), "-I", "-m", "verification_ecology_kit.capacity.installed_check"],
            cwd=root,
            env=env,
            check=True,
        )  # nosec B603
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
