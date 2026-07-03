from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    schema_dir = Path("src/verification_ecology_kit/schemas")
    output = Path("docs/schemas.md")
    lines = ["# JSON Schemas", ""]
    for path in sorted(schema_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        lines.append(f"## {path.name}")
        lines.append("")
        lines.append(f"- id: `{data.get('$id', path.name)}`")
        lines.append(f"- type: `{data.get('type', 'catalogue')}`")
        lines.append("")
    output.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
