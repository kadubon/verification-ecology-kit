# Quickstart

Install the package and create a packet:

```bash
pip install verification-ecology-kit
vek packet create --template minimal
```

Run local checks during development:

```bash
uv sync --locked --all-extras --dev
uv run pytest
uv run ruff check .
```

Compute a digest:

```bash
vek digest object.json
```
