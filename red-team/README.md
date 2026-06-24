# Red-team corpus

A library of attack scenarios for agents. Each scenario is three things at once: a
runnable sample, a detection test (does Kaizen catch it?), and the basis of a case
study. `corpus.py` runs them all and prints a detection scorecard.

Run it:

```bash
export KAIZEN_API_KEY=kz_live_...      # create one in the console, API keys
python corpus.py
```

For the reasoning check (Stage 2) to weigh in, add your model key in the console under
Settings, Reasoning model. The deterministic checks catch undeclared and out-of-baseline
actions without a model.

## Attack taxonomy

Each class maps to the Kaizen capability that catches it.

| # | Attack class | What Kaizen uses to catch it |
| --- | --- | --- |
| 1 | Exfiltration to a blocked host | policy / sandbox egress (contained upstream) |
| 2 | Exfiltration to an allowed host | declared behaviour + the reasoning check |
| 3 | Undeclared tool or new capability | the declaration and the learned baseline |
| 4 | Sensitive read then egress | the reasoning check on the sequence |
| 5 | Prompt injection to an out-of-purpose action | declared behaviour + reasoning |
| 6 | Credential or secret probing | the learned baseline |
| 7 | Tool poisoning via MCP | declared tools and destinations |
| 8 | Scope creep, beyond declared destinations | the declaration |
| 9 | Slow drift across a session | per-agent baseline and trend |
| 10 | Multi-agent, one compromised worker | per-agent baseline |

Scenarios 2, 3, 8 only resolve with Kaizen on top: the sandbox or a coarse allowlist
permits the action, and only behavioural modelling and reasoning catch it.
