# Kaizen Security

**Runtime security for the AI agents you build.** Attach Kaizen to your agent and it inspects every action, a tool call, a connection, a file or data access, and blocks what falls outside the agent's normal behavior. In your environment, as it happens.

Docs: [docs.getkaizen.io](https://docs.getkaizen.io) · Console: [app.getkaizen.io](https://app.getkaizen.io) · Source: [github.com/getkaizen/kaizen-security](https://github.com/getkaizen/kaizen-security)

## Install

```bash
npm install kaizen-security
```

## Quickstart

```ts
import { Kaizen } from "kaizen-security";

const kz = new Kaizen({ apiKey: "kz_live_...", agent: "support-bot" });

const v = kz.inspect({ tool: "export_file", target: "45.9.148.108" });
if (v.decision === "block") throw new Error(v.reason);
```

Create a key in the console under **API keys**. Without a key the client still enforces any policies you pass locally.

## Vercel AI SDK

Wrap your tools so Kaizen inspects every call. A blocked call returns a refusal to the model instead of executing.

```ts
import { guardTools } from "kaizen-security/vercel";

const tools = guardTools(kz, {
  lookupOrder,
  issueRefund,
});
```

## How it works

A fast local check blocks known-bad before it runs. An isolated Observer learns each agent's behavior and flags real deviations, in your own environment. See the [architecture](https://docs.getkaizen.io/architecture).

There is a Python SDK too: `pip install kaizen-security`.

## License

Apache-2.0
