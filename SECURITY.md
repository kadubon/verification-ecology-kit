# Security Policy

## Runtime Defaults

- No telemetry.
- No network access unless an explicit adapter is supplied by the caller.
- JSON input by default.
- No pickle for untrusted data.
- Deterministic canonicalization and SHA-256 digests by default.

## Repository Scans

CI runs:

- `scripts/verify_no_secrets.py`
- `scripts/scan_local_info.py`
- `scripts/verify_package_contents.py`
- `bandit`
- `pip-audit`
- `zizmor` where available

The scanners look for token-like values, private key markers, cloud credential markers, environment files, local machine paths, private email-like values, TeX build artifacts, notebook checkpoints, and private allowlists.

## GitHub Actions Residual Risk

The workflow uses stable version tags for third-party actions instead of full commit SHA pinning. This is documented as a residual supply-chain risk. The workflow includes action auditing with `zizmor` where available, read-only root permissions, no `pull_request_target`, and Trusted Publishing through OIDC instead of PyPI token secrets.

## PyPI Trusted Publishing

Pending publisher configuration:

- Project name: `verification-ecology-kit`
- Owner: `kadubon`
- Repository: `verification-ecology-kit`
- Workflow: `workflow.yml`
- Environment: `pypi`

The publish job requires `id-token: write` and does not use username, password, or token secrets.
