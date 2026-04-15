"""
agents.py — Orchestrator routing + shared agentic execution loop.
"""

import json
import anthropic

from prompts import (
    ORCHESTRATOR_SYSTEM, BILLING_SYSTEM, LOGISTICS_SYSTEM,
    COMPLAINTS_SYSTEM, SAFETY_SYSTEM
)
from tools import (
    BILLING_TOOLS,    billing_executor,
    LOGISTICS_TOOLS,  logistics_executor,
    COMPLAINTS_TOOLS, complaints_executor,
    SAFETY_TOOLS,     safety_executor,
)

client = anthropic.Anthropic()
MODEL  = "claude-opus-4-5"

# ── Orchestrator routing tools ─────────────────────────────────────────────

ROUTING_TOOLS = [
    {
        "name": "route_to_billing",
        "description": "Route to Billing Agent: charge disputes, refunds, promo codes, payment failures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_summary": {"type": "string"},
                "customer_id":   {"type": "string"},
                "order_id":      {"type": "string"}
            },
            "required": ["issue_summary", "customer_id"]
        }
    },
    {
        "name": "route_to_logistics",
        "description": "Route to Logistics Agent: late orders, missing items, wrong items, delivery status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_summary": {"type": "string"},
                "customer_id":   {"type": "string"},
                "order_id":      {"type": "string"}
            },
            "required": ["issue_summary", "customer_id"]
        }
    },
    {
        "name": "route_to_complaints",
        "description": "Route to Complaints Agent: food quality, rude dasher (non-safety), bad restaurant experience.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_summary": {"type": "string"},
                "customer_id":   {"type": "string"},
                "order_id":      {"type": "string"}
            },
            "required": ["issue_summary", "customer_id"]
        }
    },
    {
        "name": "route_to_safety",
        "description": "Route to Safety Agent: food tampering, allergic reaction, dasher threats, emergencies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_summary": {"type": "string"},
                "customer_id":   {"type": "string"},
                "order_id":      {"type": "string"},
                "severity":      {"type": "string", "enum": ["high", "critical"]}
            },
            "required": ["issue_summary", "customer_id", "severity"]
        }
    }
]

# Agent registry — maps routing key → (system_prompt, tools, executor)
AGENT_REGISTRY = {
    "route_to_billing":    (BILLING_SYSTEM,    BILLING_TOOLS,    billing_executor),
    "route_to_logistics":  (LOGISTICS_SYSTEM,  LOGISTICS_TOOLS,  logistics_executor),
    "route_to_complaints": (COMPLAINTS_SYSTEM, COMPLAINTS_TOOLS, complaints_executor),
    "route_to_safety":     (SAFETY_SYSTEM,     SAFETY_TOOLS,     safety_executor),
}


# ── Shared agentic loop ────────────────────────────────────────────────────

def run_agent_loop(system: str, tools: list, initial_message: str,
                   executor, max_turns: int = 8) -> dict:
    """
    Runs until Claude stops calling tools (task resolved) or max_turns hit.
    Returns: { status, response, turns, tool_calls }
    """
    messages   = [{"role": "user", "content": initial_message}]
    tool_calls = []

    for turn in range(max_turns):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system,
            tools=tools,
            messages=messages
        )

        # Append assistant turn to history
        messages.append({"role": "assistant", "content": response.content})

        # Collect any text the agent produced this turn
        agent_text = " ".join(
            block.text for block in response.content if block.type == "text"
        )

        # No tool calls → agent declared the issue resolved
        if response.stop_reason == "end_turn":
            return {
                "status":     "resolved",
                "response":   agent_text or "Your issue has been resolved.",
                "turns":      turn + 1,
                "tool_calls": tool_calls
            }

        # Execute every tool call in this turn
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"    [tool] {block.name}({json.dumps(block.input)[:80]})")
                result = executor(block.name, block.input)
                tool_calls.append({"tool": block.name, "input": block.input, "output": result})
                tool_results.append({
                    "type":        "tool_result",
                    "tool_use_id": block.id,
                    "content":     json.dumps(result)
                })

        messages.append({"role": "user", "content": tool_results})

    # Hit max_turns without resolution → escalate to human
    return {
        "status":     "escalated",
        "response":   "I'm connecting you with a human support specialist who can help further.",
        "turns":      max_turns,
        "tool_calls": tool_calls
    }


# ── Orchestrator ───────────────────────────────────────────────────────────

def orchestrate(customer_message: str, customer_id: str, order_id: str = None) -> dict:
    """
    Classifies intent and returns routing decision.
    """
    messages = [{"role": "user", "content": customer_message}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=ORCHESTRATOR_SYSTEM,
        tools=ROUTING_TOOLS,
        messages=messages
    )

    ack_text = next(
        (block.text for block in response.content if block.type == "text"), ""
    )

    for block in response.content:
        if block.type == "tool_use":
            payload = block.input
            if order_id and "order_id" not in payload:
                payload["order_id"] = order_id
            if "customer_id" not in payload:
                payload["customer_id"] = customer_id
            return {
                "route":       block.name,
                "payload":     payload,
                "ack_message": ack_text
            }

    # Orchestrator answered directly (e.g. greeting) — no routing needed
    return {"route": "direct", "ack_message": ack_text, "payload": {}}


# ── Main dispatcher ────────────────────────────────────────────────────────

def handle_support_request(customer_message: str,
                            customer_id: str,
                            order_id: str = None) -> dict:
    """
    Full pipeline:
      1. Orchestrator classifies + routes
      2. Sub-agent resolves via tool loop
      3. Return structured result
    """
    print(f"\n{'='*60}")
    print(f"[Orchestrator] Customer: {customer_id}")
    print(f"[Orchestrator] Message : {customer_message[:80]}")

    routing = orchestrate(customer_message, customer_id, order_id)

    # Direct answer (e.g. greeting) — no sub-agent needed
    if routing["route"] == "direct":
        return {
            "agent":    "orchestrator",
            "status":   "resolved",
            "response": routing["ack_message"],
            "turns":    1,
            "tool_calls": []
        }

    route_key  = routing["route"]
    agent_name = route_key.replace("route_to_", "").capitalize()

    if route_key not in AGENT_REGISTRY:
        return {
            "agent":    "fallback",
            "status":   "escalated",
            "response": "Please contact support@doordash.com or call 1-855-973-1040.",
            "turns":    1,
            "tool_calls": []
        }

    system, tools, executor = AGENT_REGISTRY[route_key]
    payload = routing["payload"]

    print(f"[Router]       → {agent_name} Agent")
    if routing["ack_message"]:
        print(f"[Ack]          {routing['ack_message'][:80]}")

    # Build enriched context for the sub-agent
    enriched = (
        f"Customer ID : {payload.get('customer_id', customer_id)}\n"
        f"Order ID    : {payload.get('order_id', order_id or 'N/A')}\n"
        f"Issue       : {payload.get('issue_summary', customer_message)}\n"
        f"Original msg: {customer_message}"
    )

    result = run_agent_loop(
        system=system,
        tools=tools,
        initial_message=enriched,
        executor=executor
    )

    print(f"[{agent_name}] Status: {result['status']} | Turns: {result['turns']}")
    print(f"[{agent_name}] Response: {result['response'][:120]}")

    return {
        "agent":      agent_name,
        "status":     result["status"],
        "response":   result["response"],
        "ack":        routing["ack_message"],
        "turns":      result["turns"],
        "tool_calls": result["tool_calls"]
    }
