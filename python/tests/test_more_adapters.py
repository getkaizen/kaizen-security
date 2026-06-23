import asyncio

from kaizen_security import Kaizen, Policy
from kaizen_security.integrations.crewai import guard_tool as crew_guard
from kaizen_security.integrations.llamaindex import guard_tool as llama_guard
from kaizen_security.integrations.pydantic_ai import guard as pyd_guard
from kaizen_security.integrations.semantic_kernel import kaizen_filter


def _kz():
    return Kaizen(policies=[Policy(mode="blocklist", rules={"skill_patterns": ["delete_all"]})])


class CrewTool:
    def __init__(self, name):
        self.name = name

    def run(self, **kw):
        return "RAN"


def test_crewai_guard():
    assert "Blocked by Kaizen" in crew_guard(_kz(), CrewTool("delete_all")).run(path="/")
    assert crew_guard(_kz(), CrewTool("read_file")).run() == "RAN"


class LlamaMeta:
    name = "delete_all"


class LlamaTool:
    metadata = LlamaMeta()

    def call(self, **kw):
        return "RAN"


def test_llamaindex_guard():
    assert "Blocked by Kaizen" in llama_guard(_kz(), LlamaTool()).call(path="/")


def test_pydantic_guard():
    @pyd_guard(_kz(), tool="delete_all")
    def delete_all(path):
        return "RAN"

    @pyd_guard(_kz(), tool="read_file")
    def read_file(path):
        return "RAN"

    assert "Blocked by Kaizen" in delete_all(path="/")
    assert read_file(path="/x") == "RAN"


def test_semantic_kernel_filter():
    f = kaizen_filter(_kz(), enforce=True)

    class Fn:
        name = "delete_all"

    class Ctx:
        function = Fn()
        arguments = {}
        result = None

    called = {"next": False}

    async def nxt(ctx):
        called["next"] = True

    asyncio.run(f(Ctx(), nxt))
    assert called["next"] is False  # blocked: the function was not invoked
