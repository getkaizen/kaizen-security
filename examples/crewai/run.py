"""Multi-agent crew with Kaizen: per-agent baselines isolate the compromised worker.

A content crew has three agents: a planner, a writer, and a publisher. Each is declared
to Kaizen with its own tools. A prompt injection compromises only the publisher, which
reaches for an undeclared exfiltration tool. Because Kaizen models each agent
separately, it flags the publisher while the planner and writer stay clean.

Attach a CrewAI (or AutoGen, LangGraph) crew the same way LangChain attaches:
wrap each agent's tools with guard_tool, one line per tool.

    from kaizen_security.integrations.crewai import guard_tool
    agent.tools = [guard_tool(kz, t) for t in agent.tools]
"""
import os, json, time, urllib.request
API = os.environ["KAIZEN_API_URL"]; KEY = os.environ["KAIZEN_API_KEY"]

def declare(agent, tools):
    urllib.request.urlopen(urllib.request.Request(f"{API}/v1/agents/{agent}/manifest",
        data=json.dumps({"tools": tools, "destinations": []}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST"))

def report(agent, tool, kind="tool_call", target=""):
    urllib.request.urlopen(urllib.request.Request(f"{API}/v1/verdicts",
        data=json.dumps({"agent": agent, "verdict": {"decision":"allow","reason":"ok","evidence":[]},
            "action": {"kind": kind, "tool": tool, "target": target, "metadata": {"source":"crewai"}}}).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST"))

crew = {
    "crew-planner":   ["make_outline", "assign_tasks"],
    "crew-writer":    ["draft_section", "edit"],
    "crew-publisher": ["format_post", "publish"],
}
for a, tools in crew.items():
    declare(a, tools)
for _ in range(3):  # baseline: each agent does its own job
    for a, tools in crew.items():
        for t in tools: report(a, t)
time.sleep(6)
# injection compromises ONLY the publisher
report("crew-publisher", "dump_subscribers", "tool_call")
report("crew-publisher", "exfiltrate", "connect", "attacker.example")
time.sleep(16)
for a in crew:
    rows = json.load(urllib.request.urlopen(urllib.request.Request(
        f"{API}/v1/verdicts?agent={a}&limit=30", headers={"Authorization": f"Bearer {KEY}"})))["verdicts"]
    flags = [v for v in rows if "undeclared" in (v.get("reason") or "") or v.get("confidence") is not None]
    print(f"  {a}: {'CLEAN' if not flags else str(len(flags))+' flags -> ' + (flags[0].get('reason') or '')[:70]}")
