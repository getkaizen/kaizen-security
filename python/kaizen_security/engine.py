from __future__ import annotations

import ipaddress
import re
import unicodedata
from typing import Optional
from urllib.parse import urlparse

from .models import Action, Finding, Policy, Verdict

# zero-width and format characters used to disguise lookalike strings
_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿"), None)

_MAX_PATTERN = 200   # cap remote regex length to bound catastrophic backtracking
_MAX_TOOL = 512      # cap the string we match against


def _norm(s: Optional[str]) -> Optional[str]:
    if not isinstance(s, str):
        return s
    return unicodedata.normalize("NFKC", s).translate(_ZERO_WIDTH).strip().lower()


def _as_ip(host: str):
    """Parse a host as an IP, tolerating integer form. Returns None if not an IP."""
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    if host.isdigit():
        try:
            return ipaddress.ip_address(int(host))
        except ValueError:
            return None
    return None


def _host_of(target: str):
    """Pull the host out of a URL or host:port, return (ip_or_none, host_lower)."""
    t = target.strip()
    if "://" in t:
        t = urlparse(t).hostname or t
    else:
        t = t.split("/", 1)[0]
    if t.startswith("[") and "]" in t:                 # IPv6 with brackets
        host = t[1 : t.index("]")]
    elif t.count(":") == 1:                            # host:port
        host = t.rsplit(":", 1)[0]
    else:
        host = t
    host = host.rstrip(".").lower()
    return _as_ip(host), host


def _networks(values) -> list:
    nets = []
    for v in values or []:
        try:
            nets.append(ipaddress.ip_network(str(v).strip(), strict=False))
        except ValueError:
            continue
    return nets


def _domain_hit(host: str, domains) -> Optional[str]:
    h = host.rstrip(".").lower()
    for d in domains or []:
        dn = (_norm(str(d)) or "").rstrip(".")
        if dn and (h == dn or h.endswith("." + dn)):  # match the domain and any subdomain
            return dn
    return None


def evaluate(action: Action, policies: list[Policy]) -> Verdict:
    """Stateless evaluation of allowlist and blocklist policies.

    Session-aware correlation lives in the client, which holds the session.
    Defensive throughout: a malformed remote policy must not throw, because the
    client's outer handler would otherwise fail the whole evaluation open.
    """
    findings: list[Finding] = []
    for p in policies:
        if not p.enabled:
            continue
        rules = p.rules or {}
        if p.mode == "blocklist":
            findings += _blocklist(action, rules)
        elif p.mode == "allowlist":
            f = _allowlist(action, rules)
            if f:
                findings.append(f)
    if findings:
        kinds = ", ".join(sorted({f.kind for f in findings}))
        return Verdict("block", f"blocked by policy: {kinds}", findings)
    return Verdict("allow", "no policy matched")


def _blocklist(a: Action, rules: dict) -> list[Finding]:
    out: list[Finding] = []

    pub = _norm(a.publisher)
    if pub and pub in {_norm(x) for x in (rules.get("publishers") or [])}:
        out.append(Finding("blacklisted publisher", a.publisher, "blocklist"))

    if a.target:
        ip, host = _host_of(a.target)
        if ip is not None:
            if any(ip in net for net in _networks(rules.get("ips"))):
                out.append(Finding("known-bad address", str(ip), "blocklist"))
        else:
            hit = _domain_hit(host, rules.get("domains"))
            if hit:
                out.append(Finding("malicious domain", host, "blocklist"))

    if a.hash:
        h = a.hash.strip().lower()
        if h in {str(x).strip().lower() for x in (rules.get("hashes") or [])}:
            out.append(Finding("known-bad hash", a.hash[:16] + "…", "blocklist"))

    if a.tool:
        tool = a.tool[:_MAX_TOOL]
        for pat in (rules.get("skill_patterns") or []):
            if not isinstance(pat, str) or len(pat) > _MAX_PATTERN:
                continue
            try:
                if re.fullmatch(pat, tool):
                    out.append(Finding("malicious skill pattern", a.tool, "blocklist"))
                    break
            except re.error:
                continue
    return out


def _allowlist(a: Action, rules: dict) -> Optional[Finding]:
    """Default-deny. Every dimension the policy constrains must match (AND).

    Policy validation guarantees at least one of publishers or tools is set, so
    an empty allowlist can never silently block everything.
    """
    allowed_pubs = {_norm(x) for x in (rules.get("publishers") or [])}
    allowed_tools = {_norm(x) for x in (rules.get("tools") or [])}

    if allowed_pubs and _norm(a.publisher) not in allowed_pubs:
        return Finding("publisher not on the allowlist", a.publisher or "none", "allowlist")
    if allowed_tools and _norm(a.tool) not in allowed_tools:
        return Finding("tool not on the allowlist", a.tool or "none", "allowlist")
    return None
