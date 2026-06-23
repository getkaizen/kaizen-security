"""Attach Kaizen to a Pydantic AI tool function.

    from kaizen_security.integrations.pydantic_ai import guard

    @agent.tool_plain
    @guard(kz)
    def lookup(q: str) -> str:
        ...

Kaizen inspects each call; with enforce, a blocked call returns a refusal instead
of running the function.
"""
from __future__ import annotations

import functools

from ..models import Action


def guard(kaizen, fn=None, *, tool=None, enforce: bool = True):
    def deco(f):
        name = tool or getattr(f, "__name__", "tool")

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            verdict = kaizen.inspect(Action(kind="tool_call", tool=name, metadata={"arguments": kwargs}))
            if enforce and verdict.blocked:
                return f"Blocked by Kaizen: {verdict.reason}"
            return f(*args, **kwargs)

        return wrapper

    return deco(fn) if fn is not None else deco
