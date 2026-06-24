"""Offline checks for the red-team corpus, no network. The key invariant: every attack
tool is undeclared, so Kaizen has a deterministic reason to flag it."""
import importlib.util, pathlib

spec = importlib.util.spec_from_file_location("corpus", pathlib.Path(__file__).parent / "corpus.py")
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


def test_scenarios_well_formed():
    assert corpus.SCENARIOS, "corpus is empty"
    for s in corpus.SCENARIOS:
        assert s["name"] and s["agent"]
        assert s["declare"]["tools"], "a scenario must declare tools"
        assert s["attack"], "a scenario must have attack actions"
        for (tool, kind, target) in s["attack"]:
            assert tool not in s["declare"]["tools"], f"attack tool {tool} should be undeclared"
