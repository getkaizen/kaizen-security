"""Kaizen + Azure Container Apps sandboxes, runnable demo.

A research agent runs inside a real ACA sandbox under deny-default egress (only
github allowed). It gets prompt-injected and exfiltrates to a github gist, an
ALLOWED host. The sandbox permits it; Kaizen flags it and reasons that it is
inconsistent with the agent's declared purpose.

Prerequisites
  pip install kaizen-security azure-containerapps-sandbox azure-identity
  az login                       # with access to an ACA sandbox group
  KAIZEN_API_KEY=kz_live_...      # create one in the console under API keys
  In the console: Settings -> Reasoning model, add your model key (for Stage 2)
  Set SANDBOX_GROUP / RESOURCE_GROUP / SUBSCRIPTION / REGION below
"""
import os, time, json, urllib.request
from azure.identity import AzureCliCredential
from azure.containerapps.sandbox import SandboxGroupClient, endpoint_for_region

API = os.environ.get("KAIZEN_API_URL", "https://api.getkaizen.io")
KEY = os.environ["KAIZEN_API_KEY"]
SUB = os.environ["SUBSCRIPTION"]; RG = os.environ["RESOURCE_GROUP"]
SG = os.environ["SANDBOX_GROUP"]; LOC = os.environ.get("REGION", "swedencentral")
AGENT = "research-bot"


def kz(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or "{}")


def report(tool, kind="tool_call", target=""):
    kz("/v1/verdicts", {"agent": AGENT,
        "verdict": {"decision": "allow", "reason": "ok", "evidence": []},
        "action": {"kind": kind, "tool": tool, "target": target, "metadata": {"source": "aca-sandbox"}}})


def main():
    # declare what the research agent is expected to do
    kz(f"/v1/agents/{AGENT}/manifest",
       {"tools": ["clone_repo", "read_file", "summarize", "fetch_issues"], "destinations": ["api.github.com"]})

    client = SandboxGroupClient(endpoint_for_region(LOC), AzureCliCredential(),
                                subscription_id=SUB, resource_group=RG, sandbox_group=SG)
    sb = client.begin_create_sandbox(disk="ubuntu", labels={"demo": "kaizen"}).result()
    sb.set_egress_default("Deny")
    sb.add_egress_host_rule("*.github.com", action="Allow")
    try:
        for _ in range(2):                       # normal research activity (baseline)
            sb.exec("git --version"); report("clone_repo")
            sb.exec("cat /etc/os-release | head -1"); report("read_file")
            sb.exec("echo summarizing"); report("summarize")
            sb.exec("curl -sS -o /dev/null --max-time 8 https://api.github.com"); report("fetch_issues", "connect", "api.github.com")
        time.sleep(8)

        sb.exec("env | grep -iE 'token|key|secret' || true"); report("dump_credentials")           # undeclared
        c = sb.exec("curl -sS -o /dev/null -w '%{http_code}' --max-time 8 https://api.github.com/gists").stdout.strip()
        report("exfiltrate_to_gist", "connect", "api.github.com")                                    # allowed host, malicious
        print(f"exfiltration to github gist -> {c}  (ACA allowed it)")
        b = sb.exec("curl -sS -o /dev/null -w '%{http_code}' --max-time 6 https://pastebin.com || echo BLOCKED").stdout.strip()
        print(f"attempt to reach pastebin -> {b}  (ACA blocked it)")
        time.sleep(16)
    finally:
        client.begin_delete_sandbox(sb.sandbox_id).result()

    out = json.load(urllib.request.urlopen(urllib.request.Request(
        f"{API}/v1/verdicts?agent={AGENT}&limit=50", headers={"Authorization": f"Bearer {KEY}"})))["verdicts"]
    for v in out:
        if v.get("confidence") is not None or "undeclared" in (v.get("reason") or ""):
            tag = f"judge {round(v['confidence']*100)}%" if v.get("confidence") else "flag"
            print(f"  [{tag}] {v['reason'][:90]}")


if __name__ == "__main__":
    main()
