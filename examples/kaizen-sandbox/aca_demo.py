"""Run the Kaizen Sandbox inside an Azure Container Apps microVM, end to end.

Provisions a microVM, uploads the collectors + the monitored agent + the in-sandbox
detector + the skills, runs them all inside the VM, and confirms that ONLY the verdict
reached Kaizen. The raw trace and egress never leave the sandbox.

Env: KAIZEN_API_KEY, OPENAI_API_KEY, KAIZEN_API_URL, KZ_SUBSCRIPTION, KZ_REGION,
KZ_RESOURCE_GROUP, KZ_SANDBOX_GROUP, KZ_AGENT.
"""
import os, base64
from azure.identity import AzureCliCredential
from azure.containerapps.sandbox import SandboxGroupClient, endpoint_for_region

SUB = os.environ["KZ_SUBSCRIPTION"]
REGION = os.environ.get("KZ_REGION", "swedencentral")
RG = os.environ["KZ_RESOURCE_GROUP"]
SG = os.environ["KZ_SANDBOX_GROUP"]
AGENT = os.environ.get("KZ_AGENT", "sandbox-agent")
HERE = os.path.dirname(os.path.abspath(__file__))

UPLOAD = {
    "collectors.py": "/work/collectors.py",
    "monitored_agent.py": "/work/monitored_agent.py",
    "detector.py": "/work/detector.py",
    "skills/trace-vs-egress-gap.md": "/work/ws/skills/trace-vs-egress-gap.md",
    "skills/undeclared-behavior.md": "/work/ws/skills/undeclared-behavior.md",
}

RUN_ALL = """#!/bin/sh
cd /work
KZ_WORKSPACE=/work/ws python3 collectors.py > /work/coll.log 2>&1 &
sleep 2
echo "[collectors] $(head -1 /work/coll.log)"
KZ_WORKSPACE=/work/ws python3 monitored_agent.py
sleep 1
echo "[workspace] traces=$(wc -l < /work/ws/traces.jsonl) egress=[$(cat /work/ws/egress.jsonl | tr '\\n' ' ')]"
echo "[detector] deciding in the VM, only the verdict will leave..."
KZ_WORKSPACE=/work/ws KZ_AGENT=$KZ_AGENT OPENAI_API_KEY=$OPENAI_API_KEY \
  KAIZEN_API_KEY=$KAIZEN_API_KEY KAIZEN_API_URL=$KAIZEN_API_URL KZ_MODEL=gpt-4o-mini \
  python3 detector.py
"""


def main():
    c = SandboxGroupClient(endpoint_for_region(REGION), AzureCliCredential(),
                           subscription_id=SUB, resource_group=RG, sandbox_group=SG)
    sb = c.begin_create_sandbox(disk="ubuntu", labels={"demo": "kaizen-sandbox"}).result()
    print(f"microVM created: {sb.sandbox_id[:18]} ({REGION})")
    try:
        # deny-default egress; only the detector's destinations are allowed out
        sb.set_egress_default("Deny")
        sb.add_egress_host_rule("*.openai.com", action="Allow")
        sb.add_egress_host_rule("*.getkaizen.io", action="Allow")

        sb.exec("mkdir -p /work/ws/skills")
        for local, remote in UPLOAD.items():
            b64 = base64.b64encode(open(os.path.join(HERE, local), "rb").read()).decode()
            sb.exec(f"echo {b64} | base64 -d > {remote}")
        sb.exec("printf '%s' '{\"tools\":[\"fetch_release_notes\",\"summarize\"],\"destinations\":[\"api.github.com\"]}' > /work/ws/declaration.json")
        b64 = base64.b64encode(RUN_ALL.encode()).decode()
        sb.exec(f"echo {b64} | base64 -d > /work/run_all.sh")

        env = (f"KZ_AGENT={AGENT} OPENAI_API_KEY={os.environ['OPENAI_API_KEY']} "
               f"KAIZEN_API_KEY={os.environ['KAIZEN_API_KEY']} KAIZEN_API_URL={os.environ.get('KAIZEN_API_URL','https://api.getkaizen.io')}")
        res = sb.exec(f"{env} sh /work/run_all.sh")
        print(res.stdout)
        if res.stderr:
            print("stderr:", res.stderr[:400])
    finally:
        c.begin_delete_sandbox(sb.sandbox_id).result()
        print("microVM deleted (workspace and raw data destroyed with it)")


if __name__ == "__main__":
    main()
