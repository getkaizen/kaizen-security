# Changelog

All notable changes to the Kaizen clients are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/).

## [0.2.0]

### Fixed
- Python: `__version__` now derives from package metadata, it no longer drifts from
  the published version.
- TypeScript: `Verdict.blocked` is now present, for parity with the Python SDK and the
  documented `verdict.blocked` check.

### Changed
- Both SDKs aligned at 0.2.0.
- READMEs rewritten to the current positioning (observe-first, observation depth, the
  sidecar).

### Added
- A publish-on-release GitHub Actions workflow.
- An Azure Container Apps sandboxes example and case study.
