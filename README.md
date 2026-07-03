# verification-ecology-kit

`verification-ecology-kit` is a Python implementation of the operational parts of Verifier Ecology Theory: verifier packets, residual ledgers, deterministic digests, reference checks, conformance reports, authority gates, audits, and a small runtime loop. It does not claim to prove theorem-level properties in software. It implements the checkable criteria, residual obligations, and reports that make those claims inspectable.

## Installation

```bash
pip install git+https://github.com/kadubon/verification-ecology-kit.git
```

After the first package release:

```bash
pip install verification-ecology-kit
```

Paper homepage: https://doi.org/10.5281/zenodo.21147093

## Development

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

## CLI

```bash
vek doctor
vek schema list
vek packet create --template operational
vek digest object.json
vek conformance bundle.json --profile core --format markdown
vek scan leaks .
vek scan local-info .
```

## Python Example

```python
from verification_ecology_kit import ResidualLedger, VerifierPacket

packet = VerifierPacket.minimal()
results = packet.validate()
ledger = ResidualLedger()

for residual in packet.residual_obligations:
    ledger.add(residual, justification="packet validation")

print([result.to_dict() for result in results])
print(ledger.trace_ok().to_dict())
```

## Security Note

The runtime has no telemetry and performs no network access by default. JSON is the default input format; pickle is not used for untrusted data. The repository includes local information and secret scanners that are run in CI before build and publish.

## Package Status

Initial OSS implementation, version `0.1.0`. The API is typed and intended to stabilize around the public classes exported from `verification_ecology_kit`.

## License

Apache-2.0.
