"""Kaizen Sandbox collectors: trace receiver + egress observer.

Both run inside the microVM and write to the per-agent workspace ONLY (no network out).
The detector reads the workspace and decides; nothing raw leaves the sandbox.

Stdlib only. Start with:  python3 collectors.py
Env: KZ_WORKSPACE (the per-agent dir), OTLP_PORT (4318), PROXY_PORT (8080).
"""
import json, os, socket, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WS = os.environ["KZ_WORKSPACE"]
OTLP_PORT = int(os.environ.get("OTLP_PORT", "4318"))
PROXY_PORT = int(os.environ.get("PROXY_PORT", "8080"))
os.makedirs(WS, exist_ok=True)


def _append(name, rec):
    with open(os.path.join(WS, name), "a") as f:
        f.write(json.dumps(rec) + "\n")


# --- 1. OTLP/HTTP trace receiver: the agent's reported trajectory ---
class OTLP(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        try:
            doc = json.loads(raw)
            for rs in doc.get("resourceSpans", []):
                for ss in rs.get("scopeSpans", []):
                    for sp in ss.get("spans", []):
                        attrs = {a["key"]: list(a.get("value", {}).values())[0] for a in sp.get("attributes", [])}
                        _append("traces.jsonl", {"span": sp.get("name"), "tool": attrs.get("tool.name") or attrs.get("gen_ai.tool.name"), "attributes": attrs})
        except Exception:
            pass
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(b"{}")


# --- 2. Egress observer: the agent's REAL outbound connections (CONNECT targets) ---
def egress_proxy():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", PROXY_PORT)); srv.listen(50)
    while True:
        client, _ = srv.accept()
        threading.Thread(target=_handle, args=(client,), daemon=True).start()


def _handle(client):
    try:
        client.settimeout(8)
        data = b""
        while b"\r\n\r\n" not in data:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
        line = data.split(b"\r\n", 1)[0].decode("latin1")
        # CONNECT host:port HTTP/1.1
        if line.startswith("CONNECT"):
            target = line.split(" ")[1]
            _append("egress.jsonl", {"target": target})   # observe the real destination
            # deny-default: we do not forward. The observation is what matters.
            client.sendall(b"HTTP/1.1 200 Connection observed\r\n\r\n")
    except Exception:
        pass
    finally:
        client.close()


if __name__ == "__main__":
    threading.Thread(target=egress_proxy, daemon=True).start()
    print(f"collectors up: OTLP :{OTLP_PORT}, egress :{PROXY_PORT}, workspace {WS}")
    ThreadingHTTPServer(("127.0.0.1", OTLP_PORT), OTLP).serve_forever()
