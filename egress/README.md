# Kaizen egress proxy

Observe an agent's **real outbound connections** without kernel access. A forward
proxy you run in your own tenant: point an agent at it and every connection it
opens is reported to Kaizen as a `connect` action (`source=egress`), so the
Observer learns the agent's normal destinations and flags new ones.

TLS stays end to end. We observe the destination (host:port), not the payload.

## Run

```bash
docker build -t kaizen-egress .
docker run -p 8080:8080 \
  -e KAIZEN_API_KEY=kz_live_... \
  -e KAIZEN_AGENT=my-agent \
  kaizen-egress
```

Or directly (stdlib only, no dependencies):

```bash
KAIZEN_API_KEY=kz_live_... KAIZEN_AGENT=my-agent python proxy.py
```

## Point your agent at it

```bash
export HTTPS_PROXY=http://localhost:8080
export HTTP_PROXY=http://localhost:8080
# run your agent; its connections now appear in the console at the Ground truth tier
```

In Kubernetes, run this as a sidecar and redirect egress to it; the agent needs no
change.

## What it sees, and does not

- **Sees:** the destination of every connection (host, port, and the TLS SNI).
- **Does not see:** payloads inside TLS (use opt-in TLS inspection for that), or
  traffic that bypasses the proxy. An agent that ignores the proxy env is invisible
  at this rung; use an in-tenant eBPF collector for a no-bypass guarantee.

## Config

| Env | Default | |
| --- | --- | --- |
| `KAIZEN_API_KEY` | (required) | your org API key |
| `KAIZEN_AGENT` | `egress-agent` | the agent name to report under |
| `KAIZEN_API_URL` | `https://api.getkaizen.io` | control plane |
| `PORT` | `8080` | listen port |
