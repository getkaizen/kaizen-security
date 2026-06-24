"""A minimal agent guarded by Kaizen.

Run with a real key:  KAIZEN_API_KEY=kz_live_... python examples/refund_bot.py
"""
import os
from kaizen_security import Kaizen, KaizenBlocked

kz = Kaizen(api_key=os.environ.get("KAIZEN_API_KEY", "kz_live_demo"), agent="refund-bot")

# Tell Kaizen what this agent is expected to do. Anything else is flagged.
kz.declare(tools=["lookup_order", "issue_refund"], destinations=["api.stripe.com"])


@kz.guard(tool="issue_refund")
def issue_refund(order_id: str, amount: float):
    # ... call Stripe ...
    return {"ok": True, "order_id": order_id, "amount": amount}


if __name__ == "__main__":
    print(issue_refund("ord_123", 19.99))

    # An undeclared, suspicious action: inspect it before acting.
    verdict = kz.inspect(tool="export_all_customers", target="45.9.148.108")
    print("decision:", verdict.decision, "| reason:", verdict.reason)
    if verdict.blocked:
        raise KaizenBlocked(verdict)
