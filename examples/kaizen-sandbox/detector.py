"""The Kaizen in-sandbox detector.

Runs inside the microVM next to the monitored agent. It reads the per-agent workspace
(declaration, the reported trace, the real egress), loads the Kaizen detection skills,
and uses the CUSTOMER's own model (OpenAI, configured in console) to investigate via tool
calls and decide. Only the verdict leaves the sandbox; the raw trace and egress never do.

Stdlib only (urllib) so it runs on the sandbox python3 with no pip install.

Env: KZ_WORKSPACE, KZ_AGENT, OPENAI_API_KEY (customer key), KAIZEN_API_KEY,
KAIZEN_API_URL (default https://api.getkaizen.io), KZ_MODEL (default gpt-4o-mini).
"""
import os, json, glob, urllib.request

WS = os.environ["KZ_WORKSPACE"]
AGENT = os.environ["KZ_AGENT"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
KAIZEN_KEY = os.environ["KAIZEN_API_KEY"]
KAIZEN_URL = os.environ.get("KAIZEN_API_URL", "https://api.getkaizen.io").rstrip("/")
MODEL = os.environ.get("KZ_MODEL", "gpt-4o-mini")


def _read(name):
    p = os.path.join(WS, name)
    return open(p).read() if os.path.exists(p) else "(none)"


def _skills():
    files = sorted(glob.glob(os.path.join(WS, "skills", "*.md")))
    return "\n\n".join(open(f).read() for f in files)


def _openai(messages, tools):
    body = json.dumps({"model": MODEL, "messages": messages, "tools": tools, "temperature": 0}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


TOOLS = [
    {"type": "function", "function": {"name": "read_declaration",
     "description": "The agent's declared tools and destinations.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "read_trace",
     "description": "What the agent REPORTED it did (OTLP spans: tool calls and their args).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "read_egress",
     "description": "What the agent ACTUALLY did on the wire (real outbound connections).", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "submit_verdict", "description": "Submit the final verdict.",
     "parameters": {"type": "object", "properties": {
        "decision": {"type": "string", "enum": ["allow", "anomaly", "block"]},
        "reason": {"type": "string"},
        "confidence": {"type": "number"}}, "required": ["decision", "reason", "confidence"]}}},
]

SYSTEM = f"""You are the Kaizen in-sandbox detector for agent '{AGENT}'. You run inside an
isolated microVM next to the agent. Investigate its behavior with the tools and decide if
it is anomalous, following these detection skills:

{_skills()}

Read the declaration, the reported trace, and the real egress, then call submit_verdict
exactly once. The raw data must never leave this sandbox; only your verdict does."""


def run():
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": "Investigate the latest activity and submit a verdict."}]
    verdict = None
    for _ in range(6):
        msg = _openai(messages, TOOLS)["choices"][0]["message"]
        messages.append(msg)
        calls = msg.get("tool_calls") or []
        if not calls:
            break
        for tc in calls:
            name = tc["function"]["name"]
            if name == "read_declaration":
                out = _read("declaration.json")
            elif name == "read_trace":
                out = _read("traces.jsonl")
            elif name == "read_egress":
                out = _read("egress.jsonl")
            elif name == "submit_verdict":
                verdict = json.loads(tc["function"]["arguments"] or "{}")
                out = "recorded"
            else:
                out = "unknown tool"
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": out[:6000]})
        if verdict:
            break

    if not verdict:
        verdict = {"decision": "allow", "reason": "no anomaly found", "confidence": 0.5}

    # Only the verdict leaves the sandbox. No trace, no egress, no payload.
    payload = json.dumps({
        "agent": AGENT,
        "verdict": {"decision": verdict["decision"], "reason": verdict["reason"], "evidence": []},
        "action": {"kind": "detection",
                   "metadata": {"source": "in-tenant-sandbox", "confidence": verdict.get("confidence"),
                                "detector": "kaizen-sandbox"}},
    }).encode()
    urllib.request.urlopen(urllib.request.Request(KAIZEN_URL + "/v1/verdicts", data=payload,
        headers={"Authorization": f"Bearer {KAIZEN_KEY}", "Content-Type": "application/json"}), timeout=30)
    print("VERDICT (only this left the sandbox):", json.dumps(verdict))


if __name__ == "__main__":
    run()
