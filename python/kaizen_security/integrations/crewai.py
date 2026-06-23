"""Attach Kaizen to a CrewAI tool.

    from kaizen_security.integrations.crewai import guard_tool
    safe = guard_tool(kz, my_tool)

Wraps the tool's run method so Kaizen inspects each call. A blocked call returns
a refusal string instead of executing.
"""
from __future__ import annotations

from ..models import Action


def guard_tool(kaizen, tool, enforce: bool = True):
    name = getattr(tool, "name", None) or getattr(tool, "__name__", None) or "tool"
    target = "run" if hasattr(tool, "run") else ("_run" if hasattr(tool, "_run") else None)
    if target is None:
        return tool
    orig = getattr(tool, target)

    def guarded(*args, **kwargs):
        verdict = kaizen.inspect(Action(kind="tool_call", tool=name, metadata={"arguments": kwargs or list(args)}))
        if enforce and verdict.blocked:
            return f"Blocked by Kaizen: {verdict.reason}"
        return orig(*args, **kwargs)

    try:
        setattr(tool, target, guarded)
    except Exception:
        # CrewAI BaseTool is a Pydantic model and rejects normal attribute
        # assignment; bypass its __setattr__ to shadow the method.
        try:
            object.__setattr__(tool, target, guarded)
        except Exception:
            pass
    return tool
