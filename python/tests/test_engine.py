import pytest

from kaizen_security import Kaizen, KaizenBlocked, Policy

BLOCK = Policy(
    mode="blocklist",
    name="ioc",
    rules={
        "publishers": ["hightower6eu"],
        "ips": ["91.92.242.30"],
        "domains": ["webhook.site"],
        "skill_patterns": [r"^clawhub[0-9]*$"],
    },
)


def kz(policies):
    return Kaizen(policies=policies, report=False, sync=False)


def test_blocklist_publisher():
    v = kz([BLOCK]).inspect(tool="x", publisher="hightower6eu")
    assert v.blocked
    assert any(f.kind == "blacklisted publisher" for f in v.evidence)


def test_blocklist_publisher_case_insensitive():
    v = kz([BLOCK]).inspect(publisher="HighTower6EU")
    assert v.blocked


def test_clean_allows():
    v = kz([BLOCK]).inspect(tool="read_records", publisher="microsoft")
    assert v.allowed


def test_blocklist_c2_ip():
    v = kz([BLOCK]).inspect(kind="connect", target="91.92.242.30")
    assert v.blocked


def test_skill_pattern():
    c = kz([BLOCK])
    assert c.inspect(tool="clawhub2").blocked
    assert c.inspect(tool="dataverse-read").allowed


def test_bad_regex_does_not_crash():
    p = Policy(mode="blocklist", rules={"skill_patterns": ["[unclosed"]})
    assert kz([p]).inspect(tool="anything").allowed


def test_allowlist():
    allow = Policy(mode="allowlist", rules={"publishers": ["microsoft"], "tools": ["read_records"]})
    c = kz([allow])
    assert c.inspect(tool="read_records", publisher="microsoft").allowed
    assert c.inspect(tool="evil_tool", publisher="unknown").blocked


def test_enforce_raises():
    with pytest.raises(KaizenBlocked):
        kz([BLOCK]).enforce(publisher="hightower6eu")


def test_correlation_read_then_connect():
    corr = Policy(mode="correlation", rules={"risky_sequence": "read_then_connect"})
    c = kz([corr])
    c.inspect(kind="file", target="/etc/shadow", metadata={"sensitive": True})
    assert c.inspect(kind="connect", target="45.9.148.108").blocked


def test_correlation_connect_alone_is_fine():
    corr = Policy(mode="correlation", rules={"risky_sequence": "read_then_connect"})
    assert kz([corr]).inspect(kind="connect", target="1.2.3.4").allowed


def test_empty_policies_allow():
    assert kz([]).inspect(tool="anything").allowed
