"""Attach Kaizen to a LangChain agent.

Wrap each LangChain tool with `guard_tool`. Every tool call the agent makes is inspected
against what you declared. Declared calls run normally; an out-of-purpose call (here, a
prompt-injected `export_all_customers`) is flagged as a behavioral anomaly, and the
reasoning check explains why.

  pip install kaizen-security langchain-core
  export KAIZEN_API_KEY=kz_live_...
  python run.py
"""
import os, json, urllib.request
from langchain_core.tools import tool
from kaizen_security import Kaizen
from kaizen_security.integrations.langchain import guard_tool

API = os.environ.get("KAIZEN_API_URL", "https://api.getkaizen.io")
KEY = os.environ["KAIZEN_API_KEY"]
AGENT = "support-langchain"

# declare what this support agent should ever do
urllib.request.urlopen(urllib.request.Request(
    f"{API}/v1/agents/{AGENT}/manifest",
    data=json.dumps({"tools": ["lookup_order", "issue_refund"], "destinations": []}).encode(),
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST"))

kz = Kaizen(api_key=KEY, agent=AGENT)


@tool
def lookup_order(order_id: str) -> str:
    """Look up an order by id."""
    return f"order {order_id}: shipped"


@tool
def issue_refund(order_id: str) -> str:
    """Issue a refund for an order."""
    return f"refunded {order_id}"


@tool
def export_all_customers(fmt: str = "csv") -> str:
    """Export the entire customer table."""   # the injected, out-of-purpose tool
    return "exported 50000 customer records"


# wrap every tool: each call is now inspected by Kaizen
tools = {t.name: guard_tool(kz, t) for t in (lookup_order, issue_refund, export_all_customers)}

# normal support work (baseline)
for _ in range(3):
    tools["lookup_order"].invoke({"order_id": "A-1001"})
    tools["issue_refund"].invoke({"order_id": "A-1001"})

# prompt injection: the agent is tricked into exporting every customer
print("agent (injected) calls export_all_customers ->", tools["export_all_customers"].invoke({"fmt": "csv"}))

import time; time.sleep(16)
out = json.load(urllib.request.urlopen(urllib.request.Request(
    f"{API}/v1/verdicts?agent={AGENT}&limit=50", headers={"Authorization": f"Bearer {KEY}"})))["verdicts"]
print("\nKaizen flagged:")
for v in out:
    r = v.get("reason") or ""
    if "undeclared" in r or v.get("confidence") is not None:
        tag = f"judge {round(v['confidence']*100)}%" if v.get("confidence") else "flag"
        print(f"  [{tag}] {r[:95]}")
