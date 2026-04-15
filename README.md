# DoorDash Multi-Agent Support System

AI-powered customer support using a multi-agent architecture built on Claude.

## Architecture

Orchestrator (intent classification + routing) routes to:
- **Billing Agent** -- refunds, credits, charge disputes, promo codes
- **Logistics Agent** -- late orders, tracking, redelivery, wrong items
- **Complaints Agent** -- food quality, dasher behavior, goodwill gestures
- **Safety Agent** -- tampering, allergic reactions, dasher threats

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python test_agents.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API

POST /support
```json
{ "customer_id": "cust_001", "message": "I was charged twice", "order_id": "ord_789" }
```
