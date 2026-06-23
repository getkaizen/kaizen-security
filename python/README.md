# Kaizen Security

**Runtime security for the AI agents you build.** Attach Kaizen to your agent and it inspects every action, a tool call, a connection, a file or data access, and blocks what falls outside the agent's normal behavior. In your environment, as it happens.

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

verdict = kz.inspect(tool="export_file", publisher="external", target="45.9.148.108")
if verdict.blocked:
    raise RuntimeError(verdict.reason)
```

Create a key in the console under **API keys**. Without a key the client still enforces any policies you pass locally.

## Attach to your framework

One line, any stack. Each adapter inspects every tool call; a blocked call returns a refusal instead of running.

**OpenAI Agents**

```python
from kaizen_security.integrations.openai_agents import KaizenHooks
await Runner.run(agent, "...", hooks=KaizenHooks(kz, enforce=True))
```

**LangChain**

```python
from kaizen_security.integrations.langchain import guard_tool
tools = [guard_tool(kz, t) for t in tools]
```

**CrewAI**

```python
from kaizen_security.integrations.crewai import guard_tool
safe = guard_tool(kz, my_tool)
```

**Semantic Kernel**

```python
from kaizen_security.integrations.semantic_kernel import kaizen_filter
kernel.add_filter("function_invocation", kaizen_filter(kz))
```

**LlamaIndex**

```python
from kaizen_security.integrations.llamaindex import guard_tool
safe = guard_tool(kz, my_tool)
```

**Pydantic AI**

```python
from kaizen_security.integrations.pydantic_ai import guard

@agent.tool_plain
@guard(kz)
def lookup(q: str) -> str:
    ...
```

**MCP** — run `kaizen-mcp` as a shim in front of any MCP server.

## How it works

A fast local check blocks known-bad before it runs. An isolated Observer learns each agent's behavior and flags real deviations, in your own environment. See the [architecture](https://docs.getkaizen.io/architecture).

There is a TypeScript SDK too: `npm install kaizen-security`.

## License

Apache-2.0
