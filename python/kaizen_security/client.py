from __future__ import annotations

import functools
import threading
import warnings
from collections import deque
from typing import Optional

from . import engine
from .models import Action, Finding, Policy, Verdict
from .report import Reporter


class KaizenBlocked(Exception):
    def __init__(self, verdict: Verdict):
        self.verdict = verdict
        super().__init__(verdict.reason)


class Kaizen:
    """The data plane client. Enforces policy locally for low latency, and
    reports verdicts to the control plane for the dashboard.

        kz = Kaizen(api_key="kz_live_...")
        v = kz.inspect(tool="clawhub2", publisher="hightower6eu")
        if v.blocked: ...

    fail_open defaults to False: if our own evaluation errors, we block. This is
    a security control, so the safe failure is to deny. Set fail_open=True only
    if you accept that our bugs become a bypass, and watch your logs.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.getkaizen.io",
        policies: Optional[list[Policy]] = None,
        agent: str = "default",
        fail_open: bool = False,
        report: bool = True,
        sync: bool = True,
        on_verdict=None,
    ):
        self.api_key = api_key
        self.base_url = self._check_url(base_url.rstrip("/"))
        self.policies = list(policies) if policies else []
        self.agent = agent
        self.fail_open = fail_open
        self._session: deque[Action] = deque(maxlen=20)
        self._lock = threading.Lock()
        self._report = report
        # the reporter exists whenever there is an api_key (it also fetches policy);
        # the report flag only controls whether we send verdicts back.
        self._reporter = Reporter(self.base_url, api_key) if api_key else None
        # optional callback fired after every verdict (used by the OTel exporter)
        self._on_verdict = on_verdict
        if sync and api_key and not self.policies:
            self._sync_policies()

    @staticmethod
    def _check_url(url: str) -> str:
        if url.startswith("http://") and not url.startswith(("http://localhost", "http://127.0.0.1")):
            warnings.warn(
                "Kaizen base_url is http://, the API key and action data would travel in cleartext. Use https.",
                stacklevel=3,
            )
        return url

    def _sync_policies(self) -> None:
        if not self._reporter:
            return
        fetched = self._reporter.get_policies(self.agent)
        if fetched is not None:
            self.policies = fetched

    def inspect(self, action: Optional[Action] = None, **kw) -> Verdict:
        a = action if action is not None else Action(**kw)
        try:
            v = engine.evaluate(a, self.policies)
        except Exception:
            v = Verdict("allow" if self.fail_open else "block", "engine error, failed " + ("open" if self.fail_open else "closed"))

        # correlation may only escalate an allow to a block, never downgrade a block
        if v.allowed:
            try:
                v = self._correlate(a, v)
            except Exception:
                if not self.fail_open:
                    v = Verdict("block", "correlation error, failed closed")

        with self._lock:
            self._session.append(a)
        if self._reporter and self._report:
            self._reporter.send(self.agent, a, v)
        if self._on_verdict:
            try:
                self._on_verdict(v, a)
            except Exception:
                pass
        return v

    def enforce(self, action: Optional[Action] = None, **kw) -> Verdict:
        v = self.inspect(action, **kw)
        if v.blocked:
            raise KaizenBlocked(v)
        return v

    def declare(self, tools=None, destinations=None) -> None:
        """Declare what this agent is expected to do: the tools it uses and the
        destinations it connects to. Anything observed outside this is flagged as
        undeclared. Requires an api_key; no-op without one."""
        if self._reporter:
            self._reporter.declare(self.agent, tools=tools, destinations=destinations)

    def _correlate(self, a: Action, v: Verdict) -> Verdict:
        # v1 session rule: a sensitive read earlier, then an outbound connect now.
        for p in self.policies:
            if not p.enabled or p.mode != "correlation":
                continue
            if (p.rules or {}).get("risky_sequence") == "read_then_connect" and a.kind == "connect":
                with self._lock:
                    prior = list(self._session)
                if any(prev.kind == "file" and (prev.metadata or {}).get("sensitive") for prev in prior):
                    return Verdict(
                        "block",
                        "blocked by correlation: sensitive read then outbound connect",
                        [Finding("risky sequence", "sensitive read then connect", "correlation")],
                    )
        return v

    def guard(self, fn=None, *, tool: Optional[str] = None, kind: str = "tool_call"):
        """Decorator that inspects a tool call before running it.

        The inspected tool name defaults to the function name; pass tool= to
        match the name your agent actually invokes. We do not serialize the
        call arguments into the action, to avoid shipping secrets.
        """
        def deco(func):
            name = tool or getattr(func, "__name__", "tool")

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.enforce(Action(kind=kind, tool=name))
                return func(*args, **kwargs)

            return wrapper

        return deco(fn) if callable(fn) else deco
