# Kaizen Security

**Runtime security for the AI agents you build.** Attach Kaizen to an agent and it inspects every action (a tool call, a connection, a file or data access), learns the agent's normal behaviour, and flags what falls outside it. It can also block known-bad outright. It runs in your environment, as the action happens.

Docs: [docs.getkaizen.io](https://docs.getkaizen.io) · Console: [app.getkaizen.io](https://app.getkaizen.io) · Source: [github.com/getkaizen/kaizen-security](https://github.com/getkaizen/kaizen-security)

## Install

```bash
pip install kaizen-security
```

The core is dependency-free and stdlib-only.

## Quickstart

```python
from kaizen_security import Kaizen

kz = Kaizen(api_key="kz_live_...", agent="support-bot")

verdict = kz.inspect(tool="issue_refund", target="api.stripe.com")
if verdict.blocked:
    raise RuntimeError(verdict.reason)
```

## Wrap a tool so it is checked automatically

```python
@kz.guard(tool="send_email")
def send_email(to, body):
    ...
```

A blocked action raises `KaizenBlocked`.

## Declare what an agent should do

Tell Kaizen the tools and destinations an agent is expected to use. Anything outside the declaration is flagged as undeclared.

```python
kz.declare(tools=["lookup_order", "issue_refund"], destinations=["api.stripe.com"])
```

## How it decides

Kaizen evaluates in two stages: a deterministic check on every action (the learned baseline plus your declaration), and a selective reasoning check (your model, your key) for the cases a rule cannot settle. See [how Kaizen decides](https://docs.getkaizen.io/reasoning/).

## Observation depth

The SDK is the lightest way to attach, and it is cooperative: it sees what you route through it. For ground truth, route the agent's egress through the Kaizen [sidecar](https://docs.getkaizen.io/sidecar/). The same Observer and the same verdict serve every attachment; you only change how deeply you see. See [observation depth](https://docs.getkaizen.io/observation-depth/).

## License

Apache-2.0
