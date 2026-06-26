"""Attach Kaizen to an Amazon Bedrock agent in one line.

    import boto3
    from kaizen_security import Kaizen
    from kaizen_security.integrations.bedrock import KaizenBedrockAgent

    kz = Kaizen(api_key="kz_live_...", agent="support-bot")
    runtime = boto3.client("bedrock-agent-runtime", region_name="us-east-1")
    agent = KaizenBedrockAgent(runtime, kz)

    result = agent.invoke_agent(
        agentId=AGENT_ID, agentAliasId=ALIAS_ID, sessionId="s1", inputText="...")
    print(result.text)          # the agent's answer
    print(result.verdicts)      # [(Action, Verdict), ...] one per action the agent took

The wrapper forces enableTrace, streams the completion, and maps every action the
Bedrock agent takes (an action-group invocation, a knowledge-base lookup, or a
return-of-control call) into a Kaizen Action that is inspected and reported. The
isolated Observer learns the agent's behavior and flags deviations.

Importing this module does not require boto3; you pass in your own bedrock-agent-runtime
client.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ..models import Action, Verdict
from ..client import KaizenBlocked


def _params(items) -> dict:
    out = {}
    for p in items or []:
        if isinstance(p, dict) and "name" in p:
            out[p["name"]] = p.get("value")
    return out


def map_trace_event(event: dict) -> Optional[Action]:
    """Map one Bedrock invoke_agent stream event to a Kaizen Action, or None.

    Pure function, unit-testable without AWS. Recognizes:
      - orchestrationTrace.invocationInput.actionGroupInvocationInput  -> tool_call
      - orchestrationTrace.invocationInput.knowledgeBaseLookupInput    -> retrieval
    """
    trace = (event.get("trace") or {}).get("trace") or {}
    ot = trace.get("orchestrationTrace") or {}
    ii = ot.get("invocationInput") or {}

    agi = ii.get("actionGroupInvocationInput")
    if agi:
        return Action(
            kind="tool_call",
            tool=agi.get("function") or agi.get("apiPath") or agi.get("actionGroupName"),
            target=agi.get("actionGroupName"),
            metadata={"params": _params(agi.get("parameters")), "source": "bedrock-trace"},
        )

    kb = ii.get("knowledgeBaseLookupInput")
    if kb:
        return Action(
            kind="tool_call",
            tool="knowledge_base_lookup",
            target=kb.get("knowledgeBaseId"),
            metadata={"query": kb.get("text"), "source": "bedrock-trace"},
        )
    return None


def map_return_control(event: dict) -> list[Action]:
    """Return-of-control: the agent hands an action back to your app. Map each call."""
    rc = event.get("returnControl") or {}
    actions = []
    for inp in rc.get("invocationInputs", []) or []:
        fi = inp.get("functionInvocationInput") or {}
        api = inp.get("apiInvocationInput") or {}
        if fi:
            actions.append(Action(kind="tool_call", tool=fi.get("function"),
                                  target=fi.get("actionGroup"),
                                  metadata={"params": _params(fi.get("parameters")), "source": "bedrock-roc"}))
        elif api:
            actions.append(Action(kind="tool_call", tool=api.get("apiPath"),
                                  target=api.get("actionGroup"),
                                  metadata={"source": "bedrock-roc"}))
    return actions


@dataclass
class BedrockResult:
    text: str = ""
    verdicts: list = field(default_factory=list)   # [(Action, Verdict), ...]
    blocked: bool = False


class KaizenBedrockAgent:
    """Wrap a bedrock-agent-runtime client so every agent action flows through Kaizen."""

    def __init__(self, runtime_client, kz, *, enforce: bool = False):
        self._rt = runtime_client
        self._kz = kz
        self._enforce = enforce

    def invoke_agent(self, **kwargs) -> BedrockResult:
        kwargs.setdefault("enableTrace", True)
        resp = self._rt.invoke_agent(**kwargs)
        result = BedrockResult()
        for event in resp.get("completion", []):
            if "chunk" in event:
                result.text += event["chunk"].get("bytes", b"").decode("utf-8", "ignore")
                continue
            actions = []
            a = map_trace_event(event)
            if a:
                actions.append(a)
            actions.extend(map_return_control(event))
            for action in actions:
                verdict = self._kz.inspect(action)
                result.verdicts.append((action, verdict))
                if verdict.blocked:
                    result.blocked = True
                    if self._enforce:
                        raise KaizenBlocked(verdict)
        return result
