# Kaizen Security

**Runtime security for the AI agents you build.** Kaizen attaches to your agent, learns what it normally does, and blocks the actions that do not fit: a tool it has never called, a connection it never makes, data it should not touch.

These are the open Kaizen clients. The managed control plane and console are at **[getkaizen.io](https://getkaizen.io)**. Full docs: **[docs.getkaizen.io](https://docs.getkaizen.io)**.

## Python

```bash
pip install kaizen-security
```

```python
from kaizen_security import Kaizen

kz = Kaizen(api_key="kz_live_...", agent="support-bot")
verdict = kz.inspect(tool="export_file", publisher="external", target="45.9.148.108")
if verdict.blocked:
    raise RuntimeError(verdict.reason)
```

Adapters for OpenAI Agents, LangChain, MCP (`kaizen-mcp`), and OpenTelemetry are in [`python/`](python/).

## TypeScript

```bash
npm install kaizen-security
```

```ts
import { Kaizen } from "kaizen-security";

const kz = new Kaizen({ apiKey: "kz_live_...", agent: "support-bot" });
const v = kz.inspect({ tool: "export_file", target: "45.9.148.108" });
if (v.decision === "block") throw new Error(v.reason);
```

A Vercel AI SDK adapter is in [`typescript/`](typescript/).

## How it works

A fast local check blocks known-bad before it runs. An isolated Observer learns each agent's behavior and flags real deviations, in your own environment. More at [docs.getkaizen.io/architecture](https://docs.getkaizen.io/architecture).

## License

Apache-2.0. See [LICENSE](LICENSE).
