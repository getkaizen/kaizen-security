import pytest

from kaizen_security import Kaizen, Policy
from kaizen_security.integrations.langchain import KaizenCallbackHandler, guard_tool


def _kz():
    return Kaizen(policies=[Policy(mode="blocklist", rules={"skill_patterns": ["delete_all"]})])


def test_callback_observes_without_error():
    h = KaizenCallbackHandler(_kz())
    h.on_tool_start({"name": "read_file"}, "{}")
    h.on_tool_start({"name": "delete_all"}, "{}")  # observe-only, never raises


def test_guard_tool_blocks_and_allows():
    pytest.importorskip("langchain_core")
    from langchain_core.tools import tool

    @tool
    def delete_all(path: str) -> str:
        "delete everything"
        return "DELETED"

    @tool
    def read_file(path: str) -> str:
        "read a file"
        return "CONTENTS"

    kz = _kz()
    blocked = guard_tool(kz, delete_all).invoke({"path": "/"})
    assert blocked.startswith("Blocked by Kaizen")
    assert "DELETED" not in blocked
    assert guard_tool(kz, read_file).invoke({"path": "/x"}) == "CONTENTS"
