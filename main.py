"""
main.py — FastAPI entry point for the DoorDash Multi-Agent Support System.

Endpoints:
  POST /support          — primary support request
  GET  /health           — liveness check
  GET  /agents           — list available agents
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn

from agents import handle_support_request

app = FastAPI(
    title="DoorDash AVA — Multi-Agent Support",
    description="Orchestrator + Billing / Logistics / Complaints / Safety sub-agents",
    version="1.0.0"
)


# ── Request / Response models ──────────────────────────────────────────────

class SupportRequest(BaseModel):
    customer_id: str  = Field(..., example="cust_001")
    message:     str  = Field(..., example="I was charged twice for my order!")
    order_id:    Optional[str] = Field(None, example="ord_789")

class SupportResponse(BaseModel):
    agent:      str
    status:     str
    response:   str
    ack:        Optional[str] = None
    turns:      int
    tool_calls: list


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "doordash-ava-support"}


@app.get("/agents")
def list_agents():
    return {
        "agents": [
            {"name": "Orchestrator", "role": "Intent classification and routing"},
            {"name": "Billing",      "role": "Refunds, charges, credits, promo codes"},
            {"name": "Logistics",    "role": "Delivery tracking, redelivery, wrong items"},
            {"name": "Complaints",   "role": "Food quality, dasher behavior, goodwill"},
            {"name": "Safety",       "role": "Tampering, allergic reactions, emergencies"},
        ]
    }


@app.post("/support", response_model=SupportResponse)
def support(req: SupportRequest):
    if not req.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    result = handle_support_request(
        customer_message=req.message,
        customer_id=req.customer_id,
        order_id=req.order_id
    )
    return result


# ── Dev runner ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
