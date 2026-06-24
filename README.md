# Kaizen Security

[![PyPI](https://img.shields.io/pypi/v/kaizen-security)](https://pypi.org/project/kaizen-security/)
[![npm](https://img.shields.io/npm/v/kaizen-security)](https://www.npmjs.com/package/kaizen-security)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-getkaizen.io-ff5722)](https://docs.getkaizen.io)

**Runtime security for the AI agents you build.** Kaizen inspects every action an agent takes (a tool call, a connection, a file or data access), learns its normal behaviour, flags what falls outside it, and can block known-bad. It runs in your own environment, as the action happens.

**Sandboxes make agents safe to run. Kaizen makes them safe to trust.** A sandbox (Azure Container Apps, OpenAI, Docker) contains an agent; Kaizen tells you when it misbehaves and catches the allowed-but-malicious. See the [ACA sandboxes case study](examples/aca-sandbox/).

These are the open Kaizen clients. The managed control plane and console are at **[getkaizen.io](https://getkaizen.io)**. Full docs: **[docs.getkaizen.io](https://docs.getkaizen.io)**.

## Install

```bash
pip install kaizen-security      # Python
npm install kaizen-security      # TypeScript
```

## Quickstart

```python
from kaizen_security import Kaizen

kz = Kaizen(api_key="kz_live_...", agent="support-bot")

verdict = kz.inspect(tool="issue_refund", target="api.stripe.com")
if verdict.blocked:
    raise RuntimeError(verdict.reason)
```

```ts
import { Kaizen } from "kaizen-security";

const kz = new Kaizen({ apiKey: "kz_live_...", agent: "support-bot" });
const verdict = await kz.inspect({ tool: "issue_refund", target: "api.stripe.com" });
if (verdict.blocked) throw new Error(verdict.reason);
```

Create a key in the console under **API keys**.

## How you attach

From a one-line SDK call up to a ground-truth collector, you choose how deeply Kaizen observes:

| How you attach | Trust |
| --- | --- |
| SDK, framework adapter | cooperative |
| MCP shim | chokepoint |
| Egress proxy, eBPF / sandbox (via the sidecar) | ground truth |

The same decision engine and the same verdict serve every attachment. See [observation depth](https://docs.getkaizen.io/observation-depth/) and [the sidecar](https://docs.getkaizen.io/sidecar/).

## How it decides

Kaizen evaluates in two stages: a deterministic check on every action (the learned baseline plus what you declared), and a selective reasoning check (your model, your key) for the cases a rule cannot settle. See [how Kaizen decides](https://docs.getkaizen.io/reasoning/).

## What is here

```
python/       Python SDK and adapters (OpenAI Agents, LangChain, MCP, OpenTelemetry)
typescript/   TypeScript SDK and the Vercel AI adapter
egress/       the egress collector, for ground-truth observation
examples/     runnable examples
```

## Integrations

**Available now:** Python SDK, TypeScript SDK, MCP shim, OpenAI Agents, LangChain, Vercel AI SDK, CrewAI, Semantic Kernel, LlamaIndex.

**Coming soon:** Copilot Studio, Agent 365, Amazon Bedrock.

**Export verdicts to:** OpenTelemetry, webhooks, Datadog, Splunk, Grafana, Slack, PagerDuty.

## Start here

1. [Quickstart](https://docs.getkaizen.io/quickstart/), attach and see your first verdict.
2. [Examples](examples/), runnable scenarios, including the [ACA sandboxes case study](examples/aca-sandbox/).
3. [SDK reference](python/README.md), the Python and TypeScript surface.
4. [Docs](https://docs.getkaizen.io), concepts, observation depth, the sidecar, the reasoning check.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and pull requests welcome.

## License

[Apache-2.0](LICENSE).
