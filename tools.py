"""
tools.py — Tool schemas + stub executors for all four sub-agents.
In production, replace each stub body with a real API call.
"""

import json
import random
import string
from datetime import datetime, timezone

# ── Helpers ────────────────────────────────────────────────────────────────

def _uid(prefix="", n=6):
    return prefix + "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

def _now():
    return datetime.now(timezone.utc).isoformat()


# ══════════════════════════════════════════════════════════════════════════
# BILLING TOOLS
# ══════════════════════════════════════════════════════════════════════════

BILLING_TOOLS = [
    {
        "name": "lookup_order",
        "description": "Fetch order details and billing breakdown for a given order ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "DoorDash order ID"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "issue_refund",
        "description": "Process a refund to the customer's original payment method.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id":  {"type": "string"},
                "amount":    {"type": "number", "description": "Refund amount in USD"},
                "reason":    {"type": "string"}
            },
            "required": ["order_id", "amount", "reason"]
        }
    },
    {
        "name": "apply_credit",
        "description": "Apply DoorDash account credit to the customer's wallet.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "amount":      {"type": "number"},
                "reason":      {"type": "string"}
            },
            "required": ["customer_id", "amount", "reason"]
        }
    },
    {
        "name": "validate_promo",
        "description": "Check whether a promo code is valid and what discount it provides.",
        "input_schema": {
            "type": "object",
            "properties": {
                "promo_code": {"type": "string"}
            },
            "required": ["promo_code"]
        }
    }
]

def billing_executor(tool_name: str, inputs: dict) -> dict:
    if tool_name == "lookup_order":
        return {
            "order_id":      inputs["order_id"],
            "customer_id":   "cust_demo",
            "items":         ["Cheeseburger x2", "Fries", "Coke"],
            "subtotal":      22.50,
            "delivery_fee":  4.99,
            "tip":           3.00,
            "total_charged": 30.49,
            "payment_method":"Visa ••••4242",
            "status":        "delivered",
            "delivered_at":  "2025-04-14T19:32:00Z"
        }

    if tool_name == "issue_refund":
        return {
            "success":    True,
            "refund_id":  _uid("ref_"),
            "amount":     inputs["amount"],
            "method":     "Visa ••••4242",
            "eta_days":   "3-5 business days",
            "timestamp":  _now()
        }

    if tool_name == "apply_credit":
        return {
            "success":        True,
            "credit_id":      _uid("cred_"),
            "amount_applied": inputs["amount"],
            "new_balance":    inputs["amount"],   # simplified
            "expires":        "2026-04-14"
        }

    if tool_name == "validate_promo":
        return {
            "valid":          True,
            "promo_code":     inputs["promo_code"],
            "discount_type":  "percentage",
            "discount_value": 20,
            "expires":        "2025-06-01",
            "min_order":      15.00
        }

    return {"error": f"Unknown billing tool: {tool_name}"}


# ══════════════════════════════════════════════════════════════════════════
# LOGISTICS TOOLS
# ══════════════════════════════════════════════════════════════════════════

LOGISTICS_TOOLS = [
    {
        "name": "track_order",
        "description": "Get live order status, dasher GPS location, and updated ETA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "contact_dasher",
        "description": "Send an in-app message to the assigned dasher.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dasher_id": {"type": "string"},
                "message":   {"type": "string"}
            },
            "required": ["dasher_id", "message"]
        }
    },
    {
        "name": "redeliver_order",
        "description": "Cancel the current delivery and initiate a full redelivery.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "reason":   {"type": "string"}
            },
            "required": ["order_id", "reason"]
        }
    },
    {
        "name": "flag_restaurant",
        "description": "Send an alert to restaurant ops team about an issue with this restaurant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string"},
                "issue":         {"type": "string"}
            },
            "required": ["restaurant_id", "issue"]
        }
    }
]

def logistics_executor(tool_name: str, inputs: dict) -> dict:
    if tool_name == "track_order":
        return {
            "order_id":       inputs["order_id"],
            "status":         "en_route",
            "dasher_id":      "dash_demo",
            "dasher_name":    "Marcus",
            "gps":            {"lat": 37.7749, "lng": -122.4194},
            "eta_minutes":    12,
            "distance_miles": 1.3,
            "picked_up_at":   "2025-04-14T20:01:00Z"
        }

    if tool_name == "contact_dasher":
        return {
            "success":    True,
            "message_id": _uid("msg_"),
            "sent_at":    _now(),
            "dasher_id":  inputs["dasher_id"]
        }

    if tool_name == "redeliver_order":
        return {
            "success":       True,
            "new_order_id":  _uid("ord_"),
            "eta_minutes":   35,
            "reason_logged": inputs["reason"],
            "original_refunded": False   # redelivery, no charge
        }

    if tool_name == "flag_restaurant":
        return {
            "success":   True,
            "ticket_id": _uid("tkt_"),
            "team":      "restaurant_ops",
            "priority":  "normal",
            "logged_at": _now()
        }

    return {"error": f"Unknown logistics tool: {tool_name}"}


# ══════════════════════════════════════════════════════════════════════════
# COMPLAINTS TOOLS
# ══════════════════════════════════════════════════════════════════════════

COMPLAINTS_TOOLS = [
    {
        "name": "get_order_history",
        "description": "Retrieve the customer's last 10 orders to assess complaint history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"}
            },
            "required": ["customer_id"]
        }
    },
    {
        "name": "submit_complaint",
        "description": "Log a formal complaint to the quality and operations team.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id":    {"type": "string"},
                "category":    {
                    "type": "string",
                    "enum": ["food_quality", "dasher_behavior", "restaurant_experience", "app_issue"]
                },
                "details":     {"type": "string"},
                "customer_id": {"type": "string"}
            },
            "required": ["order_id", "category", "details", "customer_id"]
        }
    },
    {
        "name": "offer_goodwill",
        "description": "Issue a goodwill gesture (credit, DashPass, free delivery) to the customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "gesture":     {
                    "type": "string",
                    "enum": ["credit_5", "credit_10", "dashpass_1month", "free_delivery"]
                }
            },
            "required": ["customer_id", "gesture"]
        }
    },
    {
        "name": "flag_dasher",
        "description": "Submit a behavioral flag on a dasher for ops review (non-safety).",
        "input_schema": {
            "type": "object",
            "properties": {
                "dasher_id": {"type": "string"},
                "incident":  {"type": "string"}
            },
            "required": ["dasher_id", "incident"]
        }
    }
]

def complaints_executor(tool_name: str, inputs: dict) -> dict:
    if tool_name == "get_order_history":
        return {
            "customer_id":    inputs["customer_id"],
            "total_orders":   47,
            "prior_complaints": 1,
            "last_10_orders": [
                {"order_id": _uid("ord_"), "date": "2025-04-14", "total": 30.49, "status": "delivered"},
                {"order_id": _uid("ord_"), "date": "2025-04-11", "total": 18.22, "status": "delivered"},
                {"order_id": _uid("ord_"), "date": "2025-04-08", "total": 24.00, "status": "delivered"},
            ]
        }

    if tool_name == "submit_complaint":
        return {
            "success":    True,
            "ticket_id":  _uid("comp_"),
            "category":   inputs["category"],
            "priority":   "normal",
            "logged_at":  _now(),
            "team":       "cx_quality"
        }

    if tool_name == "offer_goodwill":
        gesture_map = {
            "credit_5":        {"type": "account_credit", "value": "$5.00"},
            "credit_10":       {"type": "account_credit", "value": "$10.00"},
            "dashpass_1month": {"type": "DashPass subscription", "value": "1 month free"},
            "free_delivery":   {"type": "free delivery", "value": "next order"}
        }
        g = gesture_map.get(inputs["gesture"], {"type": inputs["gesture"], "value": "applied"})
        return {
            "success":     True,
            "gesture_id":  _uid("gest_"),
            "gesture_type": g["type"],
            "value":        g["value"],
            "applied_at":  _now()
        }

    if tool_name == "flag_dasher":
        return {
            "success":    True,
            "flag_id":    _uid("flag_"),
            "dasher_id":  inputs["dasher_id"],
            "status":     "under_review",
            "logged_at":  _now()
        }

    return {"error": f"Unknown complaints tool: {tool_name}"}


# ══════════════════════════════════════════════════════════════════════════
# SAFETY TOOLS
# ══════════════════════════════════════════════════════════════════════════

SAFETY_TOOLS = [
    {
        "name": "create_safety_incident",
        "description": "Create a formal safety incident record. REQUIRED for every safety case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id":    {"type": "string"},
                "incident_type":  {
                    "type": "string",
                    "enum": ["food_tampering", "allergic_reaction", "dasher_threat",
                             "dasher_accident", "medical_emergency"]
                },
                "severity":       {"type": "string", "enum": ["high", "critical"]},
                "description":    {"type": "string"}
            },
            "required": ["customer_id", "incident_type", "severity", "description"]
        }
    },
    {
        "name": "escalate_to_safety_team",
        "description": "Page the 24/7 human safety team immediately with the incident ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "string"},
                "priority":    {"type": "string", "enum": ["urgent", "critical"]}
            },
            "required": ["incident_id", "priority"]
        }
    },
    {
        "name": "suspend_dasher",
        "description": "Immediately suspend a dasher's account pending safety investigation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dasher_id": {"type": "string"},
                "reason":    {"type": "string"}
            },
            "required": ["dasher_id", "reason"]
        }
    },
    {
        "name": "flag_order_tampering",
        "description": "Alert the food safety team of a suspected tampering incident.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id":    {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["order_id", "description"]
        }
    }
]

def safety_executor(tool_name: str, inputs: dict) -> dict:
    if tool_name == "create_safety_incident":
        incident_id = _uid("INC-")
        return {
            "success":     True,
            "incident_id": incident_id,
            "severity":    inputs["severity"],
            "type":        inputs["incident_type"],
            "created_at":  _now(),
            "status":      "open"
        }

    if tool_name == "escalate_to_safety_team":
        return {
            "success":       True,
            "escalation_id": _uid("ESC-"),
            "incident_id":   inputs["incident_id"],
            "team_notified": "safety_oncall",
            "eta_response":  "< 5 minutes",
            "timestamp":     _now()
        }

    if tool_name == "suspend_dasher":
        return {
            "success":    True,
            "dasher_id":  inputs["dasher_id"],
            "status":     "suspended",
            "reason":     inputs["reason"],
            "suspended_at": _now(),
            "review_sla": "24 hours"
        }

    if tool_name == "flag_order_tampering":
        return {
            "success":      True,
            "flag_id":      _uid("TAMP-"),
            "order_id":     inputs["order_id"],
            "team":         "food_safety",
            "flagged_at":   _now(),
            "next_steps":   "Food safety team will contact customer within 1 hour"
        }

    return {"error": f"Unknown safety tool: {tool_name}"}
