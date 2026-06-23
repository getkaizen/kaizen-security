"""Attach Kaizen to a LlamaIndex tool.

    from kaizen_security.integrations.llamaindex import guard_tool
    safe = guard_tool(kz, my_tool)

Wraps the tool's call so Kaizen inspects each invocation. A blocked call returns
a refusal instead of executing.
"""
from __future__ import annotations

from ..models import Action


def guard_tool(kaizen, tool, enforce: bool = True):
    meta = getattr(tool, "metadata", None)
    name = getattr(meta, "name", None) or getattr(tool, "name", None) or "tool"
    orig = getattr(tool, "call", None)
    if orig is None:
        return tool

    def guarded(*args, **kwargs):
        verdict = kaizen.inspect(Action(kind="tool_call", tool=name, metadata={"source": "llamaindex", "arguments": kwargs or list(args)}))
        if enforce and verdict.blocked:
            return f"Blocked by Kaizen: {verdict.reason}"
        return orig(*args, **kwargs)

    try:
        tool.call = guarded
    except Exception:
        pass
    return tool
