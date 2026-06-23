from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional

MODES = {"allowlist", "blocklist", "correlation"}
DECISIONS = {"allow", "block"}


# An Action is what an agent is about to do, the thing we inspect.
@dataclass
class Action:
    kind: str = "tool_call"          # tool_call | skill_load | connect | file
    tool: Optional[str] = None       # tool or skill name
    publisher: Optional[str] = None  # who published it
    target: Optional[str] = None     # ip, domain, url, or path
    hash: Optional[str] = None       # file hash
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Finding:
    kind: str
    value: str
    source: str = "policy"

    def to_dict(self) -> dict:
        return asdict(self)


# The stable verdict contract: allow or block, with a reason and the evidence.
@dataclass
class Verdict:
    decision: str = "allow"          # allow | block
    reason: str = ""
    evidence: list[Finding] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.decision == "block"

    @property
    def allowed(self) -> bool:
        return self.decision == "allow"

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "evidence": [f.to_dict() for f in self.evidence],
        }


@dataclass
class Policy:
    mode: str                        # allowlist | blocklist | correlation
    rules: dict[str, Any] = field(default_factory=dict)
    name: str = ""
    enabled: bool = True

    def __post_init__(self):
        # A mistyped mode would silently become a no-op, which for a security
        # control means a silent bypass. Reject it loudly instead.
        if self.mode not in MODES:
            raise ValueError(f"unknown policy mode {self.mode!r}, expected one of {sorted(MODES)}")
        # An empty allowlist would otherwise block everything silently.
        if self.mode == "allowlist":
            r = self.rules or {}
            if not (r.get("publishers") or r.get("tools")):
                raise ValueError("an allowlist policy must list at least one allowed publisher or tool")
