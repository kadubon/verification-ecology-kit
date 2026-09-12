"""Write a SHA-256 manifest for the exact built wheel and source distribution."""

import hashlib
from pathlib import Path


def main() -> None:
    artifacts = sorted([*Path("dist").glob("*.whl"), *Path("dist").glob("*.tar.gz")])
    if len(artifacts) != 2:
        raise ValueError("exactly one wheel and one sdist required")
    Path("dist/SHA256SUMS").write_text(
        "".join(
            f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in artifacts
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
