# Contributing

Use `uv sync --all-extras --dev` before development. Run the full local checks before submitting changes:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/verify_no_secrets.py .
uv run python scripts/scan_local_info.py .
```

Design rules:

- Preserve packet core fields, residuals, boundaries, lineage, and status information.
- Do not replace evidence records with dashboard labels.
- Add schemas for normative records before relying on new JSON fields.
- Keep runtime network access behind explicit adapters.
