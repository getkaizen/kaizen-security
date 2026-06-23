import asyncio

from kaizen_security import Kaizen, Policy
from kaizen_security.integrations.openai_agents import KaizenHooks


class FakeTool:
    def __init__(self, name):
        self.name = name


class FakeCtx:
    """Stands in for the SDK's ToolContext (has reject_tool + tool_input)."""

    def __init__(self, args=None):
        self.tool_input = args or {}
        self.rejected = None

    def reject_tool(self, msg):
        self.rejected = msg


def _kz():
    return Kaizen(policies=[Policy(mode="blocklist", rules={"skill_patterns": ["delete_all"]})])


def test_blocked_tool_is_rejected_when_enforcing():
    hooks = KaizenHooks(_kz(), enforce=True)
    ctx = FakeCtx({"path": "/"})
    asyncio.run(hooks.on_tool_start(ctx, None, FakeTool("delete_all")))
    assert ctx.rejected is not None  # tool was stopped before running


def test_clean_tool_not_rejected():
    hooks = KaizenHooks(_kz(), enforce=True)
    ctx = FakeCtx()
    asyncio.run(hooks.on_tool_start(ctx, None, FakeTool("read_file")))
    assert ctx.rejected is None


def test_observe_only_never_blocks():
    hooks = KaizenHooks(_kz(), enforce=False)
    ctx = FakeCtx()
    asyncio.run(hooks.on_tool_start(ctx, None, FakeTool("delete_all")))
    assert ctx.rejected is None
