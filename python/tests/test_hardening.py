import pytest

from kaizen_security import Kaizen, KaizenBlocked, Policy
from kaizen_security import client as client_module

BLOCK = Policy(
    mode="blocklist",
    name="ioc",
    rules={
        "publishers": ["hightower6eu"],
        "ips": ["91.92.242.30"],
        "domains": ["webhook.site"],
        "skill_patterns": [r"clawhub[0-9]*"],
        "hashes": ["abcd1234"],
    },
)


def kz(policies):
    return Kaizen(policies=policies, report=False, sync=False)


def _boom(*a, **k):
    raise RuntimeError("boom")


# ---- policy validation (no silent no-op bypass) ----
def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        Policy(mode="blocklst")


def test_empty_allowlist_raises():
    with pytest.raises(ValueError):
        Policy(mode="allowlist", rules={})


# ---- fail closed by default, never downgrade a block ----
def test_fail_closed_on_engine_error(monkeypatch):
    monkeypatch.setattr(client_module.engine, "evaluate", _boom)
    assert kz([]).inspect(tool="x").blocked


def test_fail_open_when_opted_in(monkeypatch):
    monkeypatch.setattr(client_module.engine, "evaluate", _boom)
    c = Kaizen(policies=[], report=False, sync=False, fail_open=True)
    assert c.inspect(tool="x").allowed


def test_block_not_downgraded_by_correlation(monkeypatch):
    c = kz([BLOCK, Policy(mode="correlation", rules={"risky_sequence": "read_then_connect"})])
    monkeypatch.setattr(c, "_correlate", _boom)  # would raise if reached
    assert c.inspect(publisher="hightower6eu").blocked  # evaluate blocked, correlation never runs


def test_correlation_error_fails_closed(monkeypatch):
    c = kz([Policy(mode="correlation", rules={"risky_sequence": "read_then_connect"})])
    monkeypatch.setattr(c, "_correlate", _boom)
    assert c.inspect(kind="connect", target="1.2.3.4").blocked


# ---- matcher bypasses are closed ----
def test_target_port_bypass_blocked():
    assert kz([BLOCK]).inspect(kind="connect", target="91.92.242.30:443").blocked


def test_target_url_blocked():
    assert kz([BLOCK]).inspect(kind="connect", target="http://91.92.242.30/payload").blocked


def test_subdomain_blocked():
    assert kz([BLOCK]).inspect(kind="connect", target="sub.webhook.site").blocked


def test_trailing_dot_domain_blocked():
    assert kz([BLOCK]).inspect(target="webhook.site.").blocked


def test_cidr_block():
    p = Policy(mode="blocklist", rules={"ips": ["10.0.0.0/8"]})
    assert kz([p]).inspect(kind="connect", target="10.1.2.3").blocked
    assert kz([p]).inspect(kind="connect", target="11.1.2.3").allowed


def test_hash_case_insensitive():
    assert kz([BLOCK]).inspect(hash="ABCD1234").blocked


def test_zero_width_publisher_blocked():
    assert kz([BLOCK]).inspect(publisher="hightower6eu​").blocked


# ---- allowlist is AND, malformed policy does not fail open ----
def test_allowlist_and_publisher_alone_blocks():
    allow = Policy(mode="allowlist", rules={"publishers": ["microsoft"], "tools": ["read_records"]})
    assert kz([allow]).inspect(publisher="microsoft", tool="evil").blocked


def test_null_rule_does_not_fail_open():
    p = Policy(mode="blocklist", rules={"publishers": ["bad"], "ips": None, "domains": None})
    assert kz([p]).inspect(publisher="bad").blocked
    assert kz([p]).inspect(target="1.2.3.4").allowed


def test_redos_pattern_capped():
    long_pat = "(a+)+" + "a" * 300
    p = Policy(mode="blocklist", rules={"skill_patterns": [long_pat]})
    assert kz([p]).inspect(tool="a" * 50).allowed  # over the cap, skipped, no hang


# ---- guard decorator ----
def test_guard_blocks_and_preserves_metadata():
    c = kz([BLOCK])

    @c.guard(tool="clawhub2")
    def do(x):
        "the docstring"
        return x * 2

    assert do.__name__ == "do"
    assert do.__doc__ == "the docstring"
    with pytest.raises(KaizenBlocked):
        do(5)


def test_guard_allows_clean():
    c = kz([BLOCK])

    @c.guard(tool="read_records")
    def do(x):
        return x + 1

    assert do(1) == 2
