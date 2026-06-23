"""Attach Kaizen to a LangChain / LangGraph agent.

Observe every tool call with the callback handler:

    from kaizen_security import Kaizen
    from kaizen_security.integrations.langchain import KaizenCallbackHandler

    kz = Kaizen(api_key="kz_live_...", agent="support-bot")
    agent.invoke({"input": "..."}, config={"callbacks": [KaizenCallbackHandler(kz)]})

The callback is observe-only: LangChain swallows exceptions raised inside
callbacks, so it cannot block a tool. To BLOCK, wrap the tool instead:

    from kaizen_security.integrations.langchain import guard_tool
    safe_tool = guard_tool(kz, my_tool)

langchain is an optional dependency; this module imports it lazily.
"""
from __future__ import annotations

from ..models import Action

try:  # modern LangChain
    from langchain_core.callbacks import BaseCallbackHandler as _Base
except Exception:  # pragma: no cover
    try:  # older LangChain
        from langchain.callbacks.base import BaseCallbackHandler as _Base
    except Exception:
        _Base = object


class KaizenCallbackHandler(_Base):
    """Reports every tool call to Kaizen so the Observer learns the agent's
    behavior and flags deviations. Observe-only (see guard_tool to block)."""

    def __init__(self, kaizen):
        self.kaizen = kaizen

    def on_tool_start(self, serialized, input_str, **kwargs):
        name = (serialized or {}).get("name") or "tool"
        self.kaizen.inspect(Action(kind="tool_call", tool=name, metadata={"source": "langchain", "input": input_str}))


def guard_tool(kaizen, tool, enforce: bool = True):
    """Wrap a LangChain tool so Kaizen inspects each call. With enforce (default),
    a blocked call returns a refusal string instead of executing the tool."""
    from langchain_core.tools import StructuredTool

    name = getattr(tool, "name", None) or "tool"

    def _wrapped(**kwargs):
        verdict = kaizen.inspect(Action(kind="tool_call", tool=name, metadata={"source": "langchain", "input": kwargs}))
        if enforce and verdict.blocked:
            return f"Blocked by Kaizen: {verdict.reason}"
        return tool.invoke(kwargs)

    return StructuredTool.from_function(
        func=_wrapped,
        name=name,
        description=getattr(tool, "description", "") or "",
        args_schema=getattr(tool, "args_schema", None),
    )
