# Contributing

Thanks for helping improve Kaizen.

## Development

```bash
# Python
cd python && python3 -m venv .venv && source .venv/bin/activate
pip install -e . && python -m pytest

# TypeScript
cd typescript && npm install && npm run build && npm test
```

## Pull requests

- Keep the core dependency-light (the Python core is stdlib-only).
- Add a test for new behaviour.
- The public surface (`inspect`, `declare`, `guard`, the verdict shape) is shared
  between the Python and TypeScript SDKs; keep them in parity.

## Releasing

Maintainers: bump the version in `python/pyproject.toml` and `typescript/package.json`,
then publish a GitHub Release. The `publish` workflow ships to PyPI and npm using the
`PYPI_API_TOKEN` and `NPM_TOKEN` repository secrets.
