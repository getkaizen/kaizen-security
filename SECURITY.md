# Security Policy

Kaizen is a security product, and we take the security of these clients seriously.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to **security@getkaizen.io**. Do not
open a public issue for a security report.

Include where you can:

- the affected component (Python SDK, TypeScript SDK, egress collector, or the corpus),
- a description and impact,
- steps to reproduce or a proof of concept,
- the version (`pip show kaizen-security` or `npm ls kaizen-security`).

## What to expect

- We acknowledge reports within three business days.
- We will keep you updated as we investigate and work on a fix.
- We will credit you in the release notes if you would like, once a fix ships.

Please give us a reasonable window to remediate before any public disclosure.

## Supported versions

Security fixes target the latest published release on PyPI and npm. Please upgrade to
the latest version before reporting, in case the issue is already fixed.

## Scope

In scope: the SDKs, the egress collector, and the example and corpus code in this repo.
The managed control plane and console at getkaizen.io are covered separately; report
issues there to the same address.
