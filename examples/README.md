# Examples

Runnable examples of attaching Kaizen to different kinds of agents, and of Kaizen
catching real attacks. Each needs only a Kaizen API key (create one in the console);
some need the agent framework and a model key.

## Attach by agent type

| Agent type | Example | What it shows |
| --- | --- | --- |
| LangChain / LangGraph | [`langchain/`](langchain/) | `guard_tool` + callback handler; a support agent caught exporting customers |
| OpenAI Agents SDK | [`openai-agents/`](openai-agents/) | `KaizenHooks`; an injected `export_all_customers` flagged |
| Multi-agent crew (CrewAI, AutoGen) | [`crewai/`](crewai/) | per-agent baselines; one compromised worker caught, teammates clean |
| MCP agent | [`mcp/`](mcp/) | the shim in front of the server; a poisoned tool caught |
| RAG agent | [`rag/`](rag/) | a poisoned retrieved document triggers an out-of-purpose call |

## Sandboxed agents (case studies)

| Sandbox | Example | What it shows |
| --- | --- | --- |
| Azure Container Apps | [`aca-sandbox/`](aca-sandbox/) | exfiltration to an *allowed* host, only Kaizen catches it |
| Docker (code interpreter) | [`docker-sandbox/`](docker-sandbox/) | isolation hides the compromise; Kaizen surfaces it |
| Coding agent (auto-approval) | [`coding-agent/`](coding-agent/) | the reviewer auto-approval removed |

## Detection suite

| | | |
| --- | --- | --- |
| Red-team corpus | [`../red-team/`](../red-team/) | ten attack classes, scored (13/13 caught) |

Full write-ups with screenshots: <https://docs.getkaizen.io>
