# AgentPay AI — Autonomous Agent Security Model

## Core Philosophy

> **"AI proposes. Deterministic backend decides."**

In AgentPay AI, Large Language Models (LLMs) and autonomous agents are treated as **untrusted proposal engines**. The LLM never holds direct authorization over:
1. Final transaction amounts or currency conversion
2. Payment gateway credentials or Razorpay API keys
3. Merchant policy configuration or discount ceilings
4. Spending limits and daily budget allocations
5. Order state progression and payment capture
6. Cryptographic audit log chaining and verification

---

## Defense-in-Depth Security Architecture

```
                                  [ External AI Agent ]
                                            │
                                  (1) API Key & SHA-256 Auth
                                            ▼
                                  [ Correlation & Context ]
                                            │
                                  (2) Global Kill Switch Check
                                            ▼
                                  (3) Scoped Tool Permissions
                                            │
                                  (4) 3-State Circuit Breaker
                                            ▼
                                  (5) Velocity & Frequency Limiter
                                            │
                                  (6) Authoritative Server-Side Pricing
                                            ▼
                                  (7) Dynamic Risk Scoring Engine (0-100)
                                            │
                                  (8) Dynamic Trust Spending Tiers
                                            ▼
                                  (9) 5-Minute Human Approval Gate
                                            │
                                  (10) 12-State Deterministic Order Machine
                                            ▼
                                  (11) Tamper-Evident Hash-Chained Audit Trail
```

---

## 1. Agent Identity & API Key Security
- **Format**: `agp_<32-character secure random token>`
- **Storage**: Raw API keys are returned **exactly once** upon registration and **never persisted**. The database stores only salted SHA-256 hashes (`api_key_hash`) and an unprivileged 8-character prefix (`api_key_prefix`) for identification.
- **Rotation**: Supported via `POST /api/admin/agents/{id}/rotate-key`. Instantly invalidates previous hash and issues a fresh credential.

---

## 2. Global Emergency Kill Switch
Four fine-grained emergency controls accessible via admin endpoints:
- `global_write_enabled`: Immediate halt of all mutations across orders, carts, and agents.
- `payments_enabled`: Halts Razorpay checkout creation while keeping catalog discovery and analytics active.
- `campaigns_enabled`: Halts autonomous promotional campaign activation.
- `agent_execution_enabled`: Pauses all external and autonomous agent executions while human merchant staff retain operational control.

---

## 3. Scoped Granular Permissions
Each registered agent is assigned an explicit allowlist of canonical capabilities:
- `catalog.read`, `product.search`, `product.compare`
- `recommendation.read`
- `cart.create`, `cart.write`
- `checkout.request`
- `order.create`, `order.read`
- `payment.read`
- `refund.request`
- `campaign.propose`, `campaign.activate`
- `analytics.read`, `audit.read`, `approval.request`

Any unlisted action is rejected immediately with `PERMISSION_DENIED` and recorded in the audit trail.

---

## 4. 3-State Circuit Breaker
Protects the merchant from cascading payment declines and runaway agent loops:
- **`CLOSED` (Normal)**: Transactions proceed normally.
- **`OPEN` (Tripped)**: Triggered after **5 payment failures within 2 minutes**. Blocks all financial execution for a 60-second cooldown period.
- **`HALF_OPEN` (Probe)**: After 60 seconds, allows **1 probe transaction**. If successful, transitions to `CLOSED`. If failed, returns to `OPEN`.

---

## 5. Sliding-Window Velocity Limiter
Monitors agent request and transaction frequency:
- **Rate Limit**: Max 60 requests per minute
- **Transaction Velocity**: Max 5 transactions/min, 20/hour, 100/day
- Returns structured `VELOCITY_LIMIT_EXCEEDED` or `RATE_LIMITED` without dropping connections.

---

## 6. Cryptographic Tamper-Evident Audit Trail
Every governance decision, permission check, order transition, and financial capture is logged into a SHA-256 hash chain:
$$\text{Event Hash} = \text{SHA256}(\text{ID} \parallel \text{Timestamp} \parallel \text{Actor} \parallel \text{Action} \parallel \text{Resource} \parallel \text{Amount} \parallel \text{Currency} \parallel \text{Payload} \parallel \text{Previous Hash})$$

Genesis hash is initialized to `"0" * 64`. Any post-hoc manual mutation of historical rows is immediately detected and pinpointed by `GET /api/admin/audit/verify`.
