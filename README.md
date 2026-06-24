# Kaizen Security

[![PyPI](https://img.shields.io/pypi/v/kaizen-security)](https://pypi.org/project/kaizen-security/)
[![npm](https://img.shields.io/npm/v/kaizen-security)](https://www.npmjs.com/package/kaizen-security)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-getkaizen.io-ff5722)](https://docs.getkaizen.io)

**Runtime security for the AI agents you build.** Kaizen inspects every action an agent takes (a tool call, a connection, a file or data access), learns its normal behaviour, and catches what falls outside it. It blocks known-bad and flags the rest, in your own environment, as it happens.

> **Sandboxes make agents safe to run. Kaizen makes them safe to trust.** A sandbox contains an agent and blocks unknown hosts; it cannot tell you the agent exfiltrated to an *allowed* host, or that it stopped acting like itself. That is Kaizen.

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

## Watch it catch an attack

The [red-team corpus](red-team/) is a set of attack scenarios that runs against Kaizen and scores what it catches. A research agent gets prompt-injected into exfiltrating stolen data to an *allowed* GitHub host. The sandbox permits it; Kaizen catches it.

```bash
export KAIZEN_API_KEY=kz_live_...
python red-team/corpus.py
```

```
Detection scorecard: Kaizen caught 13/13 red-team actions (100%).
```

The full write-up: the [Azure Container Apps sandboxes case study](examples/aca-sandbox/).

## How you attach

From a one-line SDK call up to a ground-truth collector, you choose how deeply Kaizen observes. The same Observer and the same verdict serve every option.

| How you attach | Trust |
| --- | --- |
| SDK, framework adapter | cooperative |
| MCP shim | chokepoint |
| Egress proxy, eBPF or sandbox (via the sidecar) | ground truth |

See [observation depth](https://docs.getkaizen.io/observation-depth/) and [the sidecar](https://docs.getkaizen.io/sidecar/).

## How it decides

Two stages: a deterministic check on every action (the learned baseline plus what you declared), and a selective reasoning check (your model, your key) for the cases a rule cannot settle. See [how Kaizen decides](https://docs.getkaizen.io/reasoning/).

## Integrations

**Available now:** Python SDK, TypeScript SDK, MCP shim, OpenAI Agents, LangChain, Vercel AI SDK, CrewAI, Semantic Kernel, LlamaIndex.

**Coming soon:** Copilot Studio, Agent 365, Amazon Bedrock.

**Export verdicts to:** OpenTelemetry, webhooks, Datadog, Splunk, Slack, PagerDuty.

## What is inside

```
python/       Python SDK and adapters (OpenAI Agents, LangChain, MCP, OpenTelemetry)
typescript/   TypeScript SDK and the Vercel AI adapter
egress/       the egress collector, for ground-truth observation
examples/     runnable scenarios, including the ACA sandboxes case study
red-team/     the attack corpus and the detection runner
```

## Start here

1. [Quickstart](https://docs.getkaizen.io/quickstart/), attach and see your first verdict.
2. [Examples](examples/) and the [red-team corpus](red-team/), runnable.
3. [SDK reference](python/README.md), the Python and TypeScript surface.
4. [Docs](https://docs.getkaizen.io), concepts, observation depth, the sidecar, the reasoning check.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and pull requests welcome.

## License

[Apache-2.0](LICENSE).
