"""Kaizen MCP shim: attach the Observer to any MCP agent with zero code change.

An MCP client talks to an MCP server over stdio (newline-delimited JSON-RPC).
This shim sits transparently in the middle: it spawns the real server, forwards
traffic both ways, and intercepts every `tools/call`. Each call is inspected by
Kaizen (and reported, so the Observer learns the agent's behavior). A blocked
call is answered with an MCP error and never reaches the server.

Usage (e.g. in an MCP client config, replacing the server command):

    kaizen-mcp -- uvx some-mcp-server --flag value

Config via env: KAIZEN_API_KEY, KAIZEN_AGENT, KAIZEN_BASE_URL.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading

from .client import Kaizen
from .models import Action


def _kaizen_from_env() -> Kaizen:
    return Kaizen(
        api_key=os.environ.get("KAIZEN_API_KEY"),
        agent=os.environ.get("KAIZEN_AGENT", "mcp-agent"),
        base_url=os.environ.get("KAIZEN_BASE_URL", "https://api.getkaizen.io"),
    )


def _block_response(req_id, reason: str) -> dict:
    # An MCP tool result with isError so the model sees a refusal, not a crash.
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {"content": [{"type": "text", "text": f"Blocked by Kaizen: {reason}"}], "isError": True},
    }


def intercept(line: str, kz: Kaizen):
    """Decide what to do with one client->server line.

    Returns (forward, response):
      forward  = the line to send on to the real server, or None to drop it
      response = a JSON-RPC dict to send straight back to the client, or None
    """
    try:
        msg = json.loads(line)
    except Exception:
        return line, None  # not JSON we understand; pass through untouched
    if isinstance(msg, dict) and msg.get("method") == "tools/call":
        params = msg.get("params") or {}
        action = Action(kind="tool_call", tool=params.get("name"), metadata={"source": "mcp", "arguments": params.get("arguments")})
        verdict = kz.inspect(action)
        if verdict.blocked:
            return None, _block_response(msg.get("id"), verdict.reason)
    return line, None


def run(server_cmd, kaizen: Kaizen = None, stdin=None, stdout=None) -> int:
    kz = kaizen or _kaizen_from_env()
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    proc = subprocess.Popen(server_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    # server -> client (verbatim)
    def pump_out():
        for line in proc.stdout:
            stdout.write(line)
            stdout.flush()

    t = threading.Thread(target=pump_out, daemon=True)
    t.start()

    # client -> server (intercepted)
    for line in stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        forward, response = intercept(line, kz)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()
        if forward is not None:
            proc.stdin.write(forward + "\n")
            proc.stdin.flush()

    proc.stdin.close()
    code = proc.wait()
    t.join(timeout=5)  # drain remaining server output before returning
    return code


def main():
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if not argv:
        sys.stderr.write("usage: kaizen-mcp -- <mcp-server-command> [args...]\n")
        sys.exit(2)
    sys.exit(run(argv))


if __name__ == "__main__":
    main()
