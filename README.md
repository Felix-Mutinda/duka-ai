# Duka AI

Duka AI is a simulated, guardrail-first customer-support assistant for a fictional Nairobi electronics shop.

The purpose of this project is not to ship a production chatbot. The purpose is to demonstrate what a responsible business assistant pipeline looks like when guardrails, routing, retrieval, tools, escalation, and observability are treated as first-class engineering concerns.

> Duka is Swahili for shop.

---

## Status

Phase 0 scaffold.

Current state:

- uv-based Python project
- Ruff linting and formatting
- pytest suite
- typed configuration
- core schemas
- CI workflow

Not yet wired:

- LangGraph pipeline
- demo UI
- RAG retrieval
- tool execution
- HF Space deployment
- evaluation harness

Those are implemented in later phases.

---

## What this project demonstrates

Duka AI is designed to show:

- a guarded pipeline, not a free-running chatbot
- explicit intent routing
- retrieval over store policies
- structured tools for orders, inventory, and mock payment status
- prompt-injection resistance
- PII redaction
- escalation with context
- inspectable traces
- scenario-based demo sessions

The demo is intentionally simulated.

---

## Non-goals

This repository does not implement:

- real WhatsApp Business API integration
- real M-Pesa/Daraja integration
- real payment processing
- real customer authentication
- real inventory backend
- real ticketing system integration
- refund or discount issuance
- multi-tenant business configuration
- production security guarantees

These are explicitly out of scope for the MVP.

---

## Tech stack

- Python 3.12
- uv
- LangGraph
- Pydantic
- Gradio
- Ruff
- pytest

---

## Quickstart
