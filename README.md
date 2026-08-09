---
title: Duka AI
emoji: 🛍️
colorFrom: gray
colorTo: green
sdk: gradio
python_version: '3.12'
app_file: app.py
pinned: false
license: mit
tags:
  - gradio
  - ai
  - assistant
  - guardrails
  - langgraph
  - small-business
---

# Duka AI

Duka AI is a simulated, guardrail-first customer-support assistant for a fictional Nairobi electronics shop.

This demo shows a governed assistant pipeline:

- input gate
- intent router
- structured tools
- policy retrieval
- output guard
- escalation
- owner-facing trace panel

The demo uses fictional data. It does not connect to real WhatsApp, real M-Pesa, real inventory systems, or real customer records.

## Demo behavior

Use the scenario buttons to test:

- benign order lookup
- inventory check
- returns policy
- mock M-Pesa payment uncertainty
- fraud escalation
- direct prompt injection
- discount abuse
- PII extraction

The owner panel shows the pipeline decision trace for each scenario.

## Live model behavior

The demo can run in deterministic mock mode.

If a live OpenAI-compatible API key is configured, the assistant may use a live model only to compose responses.

The live model does not:

- choose tools
- call tools
- retrieve policy
- decide escalation
- bypass guardrails

If the live model is unavailable, slow, or returns an invalid response, the demo falls back to the deterministic mock composer.