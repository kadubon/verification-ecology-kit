# PyPI Publishing

The package is prepared for PyPI Trusted Publishing through GitHub Actions.

Trusted Publisher setup:

- Project name: `verification-ecology-kit`
- Owner: `kadubon`
- Repository: `verification-ecology-kit`
- Workflow: `workflow.yml`
- Environment: `pypi`

Release checklist:

1. Update `CHANGELOG.md`.
2. Bump the version.
3. Run full CI locally when possible.
4. Tag `vX.Y.Z`.
5. GitHub Actions builds and publishes through Trusted Publishing.
6. Verify `pip install verification-ecology-kit`.
