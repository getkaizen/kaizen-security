"""Kaizen egress proxy, observe an agent's real outbound connections.

A forward HTTP/HTTPS proxy you run in your own tenant. Point an agent at it with
`HTTPS_PROXY=http://<host>:8080` and every connection the agent opens is reported
to Kaizen as a `connect` action with `source=egress`, so the Observer learns the
agent's normal destinations and flags new ones.

TLS stays end to end: we observe the destination (host:port), not the payload.
This is the deepest rung you can reach without kernel access, and it works for any
agent whose traffic you can route. Stdlib only, no dependencies.

Config (env): KAIZEN_API_KEY (required), KAIZEN_AGENT (default "egress-agent"),
KAIZEN_API_URL (default https://api.getkaizen.io), PORT (default 8080).
"""
import asyncio
import json
import os
import urllib.request
from urllib.parse import urlparse

API_URL = os.environ.get("KAIZEN_API_URL", "https://api.getkaizen.io").rstrip("/")
API_KEY = os.environ.get("KAIZEN_API_KEY", "")
AGENT = os.environ.get("KAIZEN_AGENT", "egress-agent")
PORT = int(os.environ.get("PORT", "8080"))


def _report(target: str):
    if not API_KEY:
        return
    body = json.dumps({
        "agent": AGENT,
        "verdict": {"decision": "allow", "reason": "observed egress", "evidence": []},
        "action": {"kind": "connect", "target": target, "metadata": {"source": "egress"}},
    }).encode()
    req = urllib.request.Request(
        f"{API_URL}/v1/verdicts",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except Exception:
        pass


async def report(target: str):
    await asyncio.to_thread(_report, target)


async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        try:
            writer.close()
        except Exception:
            pass


async def handle(client_reader, client_writer):
    try:
        line = await client_reader.readline()
        if not line:
            client_writer.close()
            return
        parts = line.decode("latin1").strip().split(" ")
        if len(parts) < 2:
            client_writer.close()
            return
        method, uri = parts[0].upper(), parts[1]
        while True:  # drain request headers
            h = await client_reader.readline()
            if h in (b"\r\n", b"\n", b""):
                break

        if method == "CONNECT":
            host, _, port = uri.partition(":")
            port = int(port or "443")
            asyncio.create_task(report(f"{host}:{port}"))
            try:
                up_reader, up_writer = await asyncio.open_connection(host, port)
            except Exception:
                client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await client_writer.drain()
                client_writer.close()
                return
            client_writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await client_writer.drain()
            await asyncio.gather(pipe(client_reader, up_writer), pipe(up_reader, client_writer))
        else:
            u = urlparse(uri)
            host, port = u.hostname or "", u.port or 80
            if not host:
                client_writer.close()
                return
            asyncio.create_task(report(f"{host}:{port}"))
            try:
                up_reader, up_writer = await asyncio.open_connection(host, port)
            except Exception:
                client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await client_writer.drain()
                client_writer.close()
                return
            path = (u.path or "/") + (("?" + u.query) if u.query else "")
            up_writer.write(f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n".encode())
            await up_writer.drain()
            await asyncio.gather(pipe(up_reader, client_writer), pipe(client_reader, up_writer))
    except Exception:
        try:
            client_writer.close()
        except Exception:
            pass


async def main():
    server = await asyncio.start_server(handle, "0.0.0.0", PORT)
    print(f"Kaizen egress proxy on :{PORT} -> agent '{AGENT}' -> {API_URL}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
