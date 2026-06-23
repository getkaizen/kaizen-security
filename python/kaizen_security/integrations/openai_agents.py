"""Attach Kaizen to an OpenAI Agents SDK agent in one line.

    from agents import Agent, Runner
    from kaizen_security import Kaizen
    from kaizen_security.integrations.openai_agents import KaizenHooks

    kz = Kaizen(api_key="kz_live_...", agent="support-bot")
    await Runner.run(agent, "do the thing", hooks=KaizenHooks(kz))

Every tool the agent calls flows to Kaizen: it is inspected against policy and
reported, so the isolated Observer learns the agent's behavior and flags
deviations. Observe-only by default; with enforce=True a blocked tool is stopped
before it runs (via the SDK's tool-rejection path, falling back to raising).

Importing this module does not require openai-agents to be installed; KaizenHooks
only needs it at runtime when you actually run an agent.
"""
from __future__ import annotations

from ..client import KaizenBlocked
from ..models import Action

try:  # the base class is provided by openai-agents when present
    from agents import RunHooks as _Base
except Exception:  # pragma: no cover - openai-agents optional
    _Base = object


def _tool_name(tool) -> str:
    return getattr(tool, "name", None) or getattr(tool, "__name__", None) or "tool"


def _tool_args(context):
    for attr in ("tool_input", "tool_arguments"):
        v = getattr(context, attr, None)
        if v is not None:
            return v
    return None


class KaizenHooks(_Base):
    """RunHooks that route every tool call through Kaizen."""

    def __init__(self, kaizen, enforce: bool = False):
        self.kaizen = kaizen
        self.enforce = enforce

    async def on_tool_start(self, context, agent, tool):
        action = Action(kind="tool_call", tool=_tool_name(tool), metadata={"source": "openai-agents", "arguments": _tool_args(context)})
        verdict = self.kaizen.inspect(action)
        if self.enforce and verdict.blocked:
            reject = getattr(context, "reject_tool", None)
            if callable(reject):
                reject(verdict.reason)  # clean: tool never executes
            else:
                raise KaizenBlocked(verdict)
        return None
