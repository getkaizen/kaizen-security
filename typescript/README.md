# Kaizen Security

**Runtime security for the AI agents you build.** Attach Kaizen to an agent and it inspects every action (a tool call, a connection, a file or data access), learns the agent's normal behaviour, and flags what falls outside it. It can also block known-bad outright. It runs in your environment, as the action happens.

Docs: [docs.getkaizen.io](https://docs.getkaizen.io) · Console: [app.getkaizen.io](https://app.getkaizen.io) · Source: [github.com/getkaizen/kaizen-security](https://github.com/getkaizen/kaizen-security)

## Install

```bash
npm install kaizen-security
```

## Quickstart

```ts
import { Kaizen } from "kaizen-security";

const kz = new Kaizen({ apiKey: "kz_live_...", agent: "support-bot" });

const verdict = await kz.inspect({ tool: "issue_refund", target: "api.stripe.com" });
if (verdict.blocked) throw new Error(verdict.reason);
```

Create a key in the console under **API keys**.

## Vercel AI SDK

Wrap your tools so Kaizen inspects every call. A blocked call returns a refusal to the model instead of executing.

```ts
import { guardTools } from "kaizen-security/vercel";

const tools = guardTools(kz, { lookupOrder, issueRefund });
```

## How it decides

Kaizen evaluates in two stages: a deterministic check on every action (the learned baseline plus your declaration), and a selective reasoning check (your model, your key) for the cases a rule cannot settle. See [how Kaizen decides](https://docs.getkaizen.io/reasoning/).

## Observation depth

The SDK is the lightest way to attach, and it is cooperative: it sees what you route through it. For ground truth, route the agent's egress through the Kaizen [sidecar](https://docs.getkaizen.io/sidecar/). The same Observer and the same verdict serve every attachment. See [observation depth](https://docs.getkaizen.io/observation-depth/).

There is a Python SDK too: `pip install kaizen-security`.

## License

Apache-2.0
