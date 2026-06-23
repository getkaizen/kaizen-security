"""Attach Kaizen to Microsoft Semantic Kernel via a function-invocation filter.

    kernel.add_filter("function_invocation", kaizen_filter(kz))

Every function the kernel invokes is inspected. With enforce, a blocked call is
short-circuited (the function does not run) and a refusal is returned.
"""
from __future__ import annotations

from ..models import Action


def kaizen_filter(kaizen, enforce: bool = True):
    async def filter(context, next):  # noqa: A002 - SK's documented signature
        fn = getattr(context, "function", None)
        name = getattr(fn, "name", None) or getattr(fn, "fully_qualified_name", None) or "function"
        args = {}
        try:
            args = dict(getattr(context, "arguments", {}) or {})
        except Exception:
            pass
        verdict = kaizen.inspect(Action(kind="tool_call", tool=name, metadata={"source": "semantic-kernel", "arguments": args}))
        if enforce and verdict.blocked:
            msg = f"Blocked by Kaizen: {verdict.reason}"
            try:
                from semantic_kernel.functions.function_result import FunctionResult

                context.result = FunctionResult(function=context.function.metadata, value=msg)
            except Exception:
                try:
                    context.result = msg
                except Exception:
                    pass
            return  # do not call next: the function is not invoked
        await next(context)

    return filter
