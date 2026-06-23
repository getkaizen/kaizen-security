import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from kaizen_security import Kaizen, Policy
from kaizen_security.integrations.otel import record_verdict


def test_otel_emits_spans_with_attributes():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    kz = Kaizen(policies=[Policy(mode="blocklist", rules={"skill_patterns": ["delete_all"]})], on_verdict=record_verdict)
    kz.inspect(tool="delete_all", kind="tool_call")
    kz.inspect(tool="read_file", kind="tool_call")

    spans = exporter.get_finished_spans()
    assert len(spans) == 2
    assert all(s.name == "kaizen.inspect" for s in spans)
    blocked = [s for s in spans if s.attributes.get("kaizen.decision") == "block"]
    assert len(blocked) == 1
    assert blocked[0].attributes.get("kaizen.tool") == "delete_all"
