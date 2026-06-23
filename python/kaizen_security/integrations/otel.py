"""Emit an OpenTelemetry span for each Kaizen verdict.

    from kaizen_security import Kaizen
    from kaizen_security.integrations.otel import record_verdict

    kz = Kaizen(api_key="kz_live_...", on_verdict=record_verdict)

Every inspect() then appears in your traces as a `kaizen.inspect` span carrying
the decision, reason, tool, and target. Blocked verdicts mark the span as an
error, so they surface in Datadog, Grafana, Honeycomb, or any OTel backend with
no per-vendor code. opentelemetry is an optional dependency.
"""
from __future__ import annotations

try:
    from opentelemetry import trace as _trace
except Exception:  # pragma: no cover - opentelemetry optional
    _trace = None


def record_verdict(verdict, action=None):
    if _trace is None:
        return
    tracer = _trace.get_tracer("kaizen-security")
    with tracer.start_as_current_span("kaizen.inspect") as span:
        span.set_attribute("kaizen.decision", verdict.decision)
        if getattr(verdict, "reason", None):
            span.set_attribute("kaizen.reason", verdict.reason)
        if action is not None:
            if action.kind:
                span.set_attribute("kaizen.kind", action.kind)
            if action.tool:
                span.set_attribute("kaizen.tool", action.tool)
            if getattr(action, "publisher", None):
                span.set_attribute("kaizen.publisher", action.publisher)
            if getattr(action, "target", None):
                span.set_attribute("kaizen.target", action.target)
        if verdict.blocked:
            span.set_status(_trace.Status(_trace.StatusCode.ERROR, verdict.reason or "blocked"))
