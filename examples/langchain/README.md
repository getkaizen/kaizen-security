# Attach Kaizen to a LangChain agent

Wrap each LangChain tool with `guard_tool`. Every tool call the agent makes is inspected
against what you declared, in one line per tool.

```python
from kaizen_security import Kaizen
from kaizen_security.integrations.langchain import guard_tool

kz = Kaizen(api_key="kz_live_...", agent="support-bot")
safe_tools = [guard_tool(kz, t) for t in my_tools]   # hand these to your agent
```

To observe a whole agent run instead, attach the callback:

```python
from kaizen_security.integrations.langchain import KaizenCallbackHandler
agent.invoke({"input": "..."}, config={"callbacks": [KaizenCallbackHandler(kz)]})
```

## This demo

A support agent declares `lookup_order` and `issue_refund`. It runs normal work, then a
prompt injection tricks it into calling `export_all_customers`. Kaizen flags the
undeclared call and the reasoning check judges it suspicious:

```
[judge 60%] reasoning judge (suspicious): exporting the full customer table, outside its support duties
[flag]      undeclared: this agent used a tool it never declared (export_all_customers)
```

## Run it

```bash
pip install kaizen-security langchain-core
export KAIZEN_API_KEY=kz_live_...
python run.py
```

Docs: <https://docs.getkaizen.io/integrations/langchain/>
