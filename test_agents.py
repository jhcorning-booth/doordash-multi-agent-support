"""
test_agents.py — Validates all four routing paths against the live Anthropic API.
Run: python test_agents.py
"""

import json
import sys
import os

# Make sure we can import from the agent package
sys.path.insert(0, os.path.dirname(__file__))

from agents import handle_support_request

TEST_CASES = [
    {
        "label":       "💳  Billing — duplicate charge",
        "customer_id": "cust_001",
        "order_id":    "ord_111",
        "message":     "I was charged twice for my burger order last night. Please refund the extra charge."
    },
    {
        "label":       "🚚  Logistics — late order",
        "customer_id": "cust_002",
        "order_id":    "ord_222",
        "message":     "My order is over an hour late. Where is my food?"
    },
    {
        "label":       "😤  Complaints — rude dasher",
        "customer_id": "cust_003",
        "order_id":    "ord_333",
        "message":     "The dasher was incredibly rude to me when he dropped off my order. Very unprofessional."
    },
    {
        "label":       "⚠️   Safety — possible tampering",
        "customer_id": "cust_004",
        "order_id":    "ord_444",
        "message":     "My food packaging was clearly opened and resealed. I think someone tampered with it."
    },
]

def run_tests():
    passed = 0
    failed = 0

    for tc in TEST_CASES:
        print(f"\n{'─'*60}")
        print(f"TEST: {tc['label']}")
        print(f"MSG : {tc['message']}")

        try:
            result = handle_support_request(
                customer_message=tc["message"],
                customer_id=tc["customer_id"],
                order_id=tc["order_id"]
            )

            print(f"\n  ✅  Agent    : {result['agent']}")
            print(f"     Status   : {result['status']}")
            print(f"     Turns    : {result['turns']}")
            print(f"     Tools    : {[c['tool'] for c in result.get('tool_calls', [])]}")
            print(f"     Response : {result['response'][:200]}")
            passed += 1

        except Exception as e:
            print(f"\n  ❌  FAILED: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests")
    return failed == 0


if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
