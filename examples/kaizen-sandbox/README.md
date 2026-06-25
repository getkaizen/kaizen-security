# The Kaizen Sandbox: in-tenant agentic detection

**Kaizen decides inside your tenant. Only the verdict leaves.**

This is the deepest Kaizen attach mode and the one that is hard to copy: a detection
agent that runs inside a microVM next to your agent, watches its **traces and its real
egress**, reasons over them against the agent's declaration with **your own model**, and
sends out **only the verdict**. The raw trace and egress never leave the sandbox.

```
   ACA microVM (the decision boundary)
   ┌─────────────────────────────────────────────────────────┐
   │  monitored agent ──OTLP──▶ collectors ─▶ per-agent       │
   │                  ──proxy─▶              workspace         │
   │                            (traces.jsonl, egress.jsonl,  │
   │                             declaration.json, skills/)   │
   │                                    │                      │
   │   detector.py  ── your OpenAI key, skills + tool calls ──┤
   │     reads declaration / trace / egress, decides          │
   └────────────────────────────────────┼─────────────────────┘
                                         │
                    only the verdict ────▶ Kaizen control plane
```

## What it caught (a real run)

A `research-bot` declared for `fetch_release_notes`, `summarize`, and `api.github.com`
was prompt-injected to lie. Its **trace reported** a fetch from `api.github.com`; its
**real egress** went to `attacker.example`. The in-sandbox detector compared the two and
returned:

> **block (0.9):** "The agent reported connecting to 'api.github.com' but actually
> connected to 'attacker.example', an undeclared destination."

Only that verdict reached Kaizen. The trace and the egress stayed in the microVM, which
was then destroyed.

## The pieces

- `collectors.py` — the OTLP trace receiver and the egress observer; write to the
  per-agent workspace only, no network out.
- `monitored_agent.py` — a sample agent that lies (reports github, connects to attacker).
- `detector.py` — the in-sandbox detector: reads the workspace, loads the skills, uses
  the customer's OpenAI key to investigate via tool calls, and posts only the verdict.
- `skills/` — the detection playbooks (`trace-vs-egress-gap.md`, `undeclared-behavior.md`).
- `aca_demo.py` — provisions an Azure Container Apps microVM, uploads the above, runs the
  whole flow inside it, and confirms only the verdict left.

## Run it in a microVM

```bash
export KAIZEN_API_KEY=kz_live_...        # the verdict destination
export OPENAI_API_KEY=sk-...             # the customer's model, used for the reasoning
export KZ_SUBSCRIPTION=...  KZ_RESOURCE_GROUP=...  KZ_SANDBOX_GROUP=...  KZ_REGION=swedencentral
python aca_demo.py
```

The model is OpenAI for now; configure your key in the console under
**Settings, Reasoning model**. Full write-up:
<https://docs.getkaizen.io/case-studies/kaizen-sandbox/>
