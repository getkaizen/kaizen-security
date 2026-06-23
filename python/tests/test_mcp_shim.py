import io
import json
import sys

from kaizen_security import Kaizen, Policy
from kaizen_security.mcp_shim import intercept, run


def _kz():
    return Kaizen(policies=[Policy(mode="blocklist", rules={"skill_patterns": ["delete_all"]})])


def _call(req_id, name):
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {"name": name, "arguments": {}}})


def test_intercept_blocks_bad_tool():
    fwd, resp = intercept(_call(1, "delete_all"), _kz())
    assert fwd is None
    assert resp is not None and resp["result"]["isError"] is True


def test_intercept_forwards_clean_tool():
    fwd, resp = intercept(_call(2, "read_file"), _kz())
    assert resp is None and fwd is not None


def test_intercept_passes_non_toolcall():
    line = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": {}})
    fwd, resp = intercept(line, _kz())
    assert resp is None and fwd == line


FAKE_SERVER = r"""
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except Exception:
        continue
    if msg.get("method") == "tools/call":
        print(json.dumps({"jsonrpc": "2.0", "id": msg.get("id"),
              "result": {"content": [{"type": "text", "text": "SERVER_RAN:" + msg["params"]["name"]}]}}), flush=True)
"""


def test_run_blocks_and_forwards_via_subprocess():
    stdin = io.StringIO(_call(1, "delete_all") + "\n" + _call(2, "read_file") + "\n")
    out = io.StringIO()
    run([sys.executable, "-c", FAKE_SERVER], kaizen=_kz(), stdin=stdin, stdout=out)
    s = out.getvalue()
    assert "Blocked by Kaizen" in s            # delete_all was blocked
    assert "SERVER_RAN:read_file" in s         # read_file reached the server
    assert "SERVER_RAN:delete_all" not in s    # delete_all never reached the server
