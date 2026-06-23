# kaizen-security

Pluggable enforcement for AI agent actions. Inspect every tool call, skill load, or outbound connection, and block the known-bad before it reaches your data. Zero runtime dependencies.

## Install

```bash
pip install kaizen-security
```

## Quickstart

```python
from kaizen_security import Kaizen

kz = Kaizen(api_key="kz_live_...")          # syncs policy from the control plane

verdict = kz.inspect(tool="clawhub2", publisher="hightower6eu", target="91.92.242.30")
if verdict.blocked:
    print(verdict.reason)                    # blocked by policy: blacklisted publisher, ...
    for f in verdict.evidence:
        print(f.kind, f.value)
```

Raise on a block instead of branching:

```python
from kaizen_security import KaizenBlocked

try:
    kz.enforce(tool="clawhub2", publisher="hightower6eu")
except KaizenBlocked as e:
    handle(e.verdict)
```

Wrap a tool function:

```python
@kz.guard
def call_tool(name, **kwargs):
    ...
```

## Run it fully local, no account

```python
from kaizen_security import Kaizen, Policy

policy = Policy(mode="blocklist", rules={
    "publishers": ["hightower6eu"],
    "ips": ["91.92.242.30"],
    "skill_patterns": [r"^clawhub[0-9]*$"],
})
kz = Kaizen(policies=[policy], report=False)
```

## The contract

`inspect(action) -> Verdict(decision, reason, evidence)` where `decision` is `allow` or `block`. Enforcement runs locally for low latency. When an `api_key` is set, the client syncs policy from the control plane and reports verdicts back for the dashboard, fire and forget so it never adds latency.

## Modes

- `blocklist`: block on a match against blacklisted publishers, IPs, domains, skill patterns, or hashes.
- `allowlist`: allow only approved publishers or tools, block the rest.
- `correlation`: flag a risky session sequence, for example a sensitive read followed by an outbound connect.
