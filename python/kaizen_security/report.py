from __future__ import annotations

import json
import queue
import ssl
import threading
import urllib.request
from typing import Optional

from .models import Action, Policy, Verdict

SCHEMA_VERSION = "1"
_SSL = ssl.create_default_context()


# Talks to the control plane. Standard library only, so the SDK stays
# dependency free. Verdict reporting goes through one bounded queue drained by a
# small worker pool, so a slow or unreachable control plane can never spawn
# unbounded threads or block the agent.
class Reporter:
    def __init__(self, base_url: str, api_key: str, timeout: float = 3.0, workers: int = 2, max_queue: int = 1000):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._q: queue.Queue = queue.Queue(maxsize=max_queue)
        self._started = False
        self._workers = workers

    def _ensure_workers(self) -> None:
        if self._started:
            return
        self._started = True
        for _ in range(self._workers):
            threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self) -> None:
        while True:
            payload = self._q.get()
            try:
                self._post("/v1/verdicts", payload)
            except Exception:
                pass
            finally:
                self._q.task_done()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _post(self, path: str, payload: dict) -> None:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode(),
            headers=self._headers(),
            method="POST",
        )
        urllib.request.urlopen(req, timeout=self.timeout, context=_SSL).close()

    def send(self, agent: str, action: Action, verdict: Verdict) -> None:
        self._ensure_workers()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "agent": agent,
            "action": action.to_dict(),
            "verdict": verdict.to_dict(),
        }
        try:
            self._q.put_nowait(payload)   # drop, never block the agent, if the queue is full
        except queue.Full:
            pass

    def get_policies(self, agent: str) -> Optional[list[Policy]]:
        try:
            req = urllib.request.Request(
                self.base_url + f"/v1/policy?agent={agent}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout, context=_SSL) as r:
                data = json.loads(r.read())
            return [
                Policy(
                    mode=p["mode"],
                    rules=p.get("rules", {}),
                    name=p.get("name", ""),
                    enabled=p.get("enabled", True),
                )
                for p in data.get("policies", [])
            ]
        except Exception:
            return None
