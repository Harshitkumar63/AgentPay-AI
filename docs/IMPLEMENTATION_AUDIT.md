# 📋 AgentPay AI — Implementation Audit & Architecture Review

**Audit Date:** 2026-09-01  
**Target Repository:** [AgentPay-AI](https://github.com/Harshitkumar63/AgentPay-AI)  
**Audit Purpose:** Comprehensive inspection of the existing codebase prior to upgrading the system into a production-quality governed agentic commerce prototype.

---

## 1. Existing Architecture Overview

AgentPay AI is a full-stack AI-governed commerce platform separating non-deterministic AI proposals from deterministic backend enforcement:

- **Backend Framework:** FastAPI (Python 3.14 / 3.11+ compatible) with SQLAlchemy ORM and Pydantic V2.
- **Frontend Framework:** Next.js 16.3.1 (Turbopack, React 19, TypeScript) with a custom Vanilla CSS design system.
- **Database Support:** SQLite (`agentpay.db`) for zero-config local demo mode with seamless PostgreSQL support for containerized/production deployments.
- **Payment Layer:** Razorpay Standard Checkout & Orders API with Test Mode simulation and HMAC-SHA256 signature verification.
- **AI Tool Integration:** OpenAI Function Calling (`gpt-4o`), Google Gemini (`gemini-1.5-pro`), and a local deterministic tool executor fallback.

---

## 2. Existing Database Models

The database models are defined in `backend/app/models/`:

1. **`Merchant`** (`merchant.py`): Merchant profile, business credentials, currency (`INR`), active status.
2. **`Product`** (`product.py`): Catalog products, prices, stock levels, categories, tags, image URLs, cross-sell and upsell metadata.
3. **`Cart` & `CartItem`** (`cart.py`): User/agent shopping carts, line items, quantities, server-computed subtotals.
4. **`Order`** (`order.py`): Order record with receipt, amount, status, payment status, idempotency key, order type, decision factors, and structured timeline events.
5. **`Payment`** (`payment.py`): Payment record linking to Razorpay order ID, payment ID, status (`created`, `authorized`, `captured`, `failed`), and error codes.
6. **`AuditLog`** (`audit.py`): Audit events recording actor type, actor ID, action, resource, amount, policy result, approval status, and extra metadata.
7. **`Agent`** (`agent.py`): Registered agents with role, status, permissions array, daily budget, per-tx limit, hourly limit, trust score, circuit breaker counters, and API key hashes.
8. **`AgentBudget`** (`agent.py`): Spending limits, spent today, spent this hour, transaction counts per minute/hour/day, reset timestamps.
9. **`AgentTrust`** (`agent.py`): Behavioral signals (successful txs, payment failures, policy violations, duplicate requests, approval rates) and calculated trust score (0–100).
10. **`AgentAction`** (`agent.py`): Session trace cards recording tool calls, inputs, outputs, execution duration, and status.
11. **`Policy`** (`policy.py`): Merchant governance policy defining purchase limits, discount caps, approval requirement, auto-refund flag, and allowed action list.
12. **`WebhookEvent`** (`webhook.py`): Ingested Razorpay webhook events, deduplication event ID, status, and payload.
13. **`Approval`** (`approval.py`): Human-in-the-loop approval records with risk level, risk score, 5-minute expiration timestamp, and decision status.
14. **`RecommendationEvent`** (`recommendation_event.py`): Telemetry for recommendation funnel (`shown`, `clicked`, `added`, `purchased`) and attributed revenue.
15. **`CampaignProposal`** (`campaign.py`): Marketing campaigns proposed by AI growth agents with discount, budget, and activation status.
16. **`Refund`** (`refund.py`): Gated refund lifecycle records (`REQUESTED`, `APPROVAL_PENDING`, `APPROVED`, `COMPLETED`, `REJECTED`).
17. **`CustomerPreference`** (`customer_preference.py`): Cross-session user preferences (categories, brands, budget caps).
18. **`Experiment` & `ExperimentVariant`** (`experiment.py`): A/B testing framework for dynamic pricing and conversion tracking.

---

## 3. Existing API Routers & Endpoints

The backend registers 27 routers in `backend/app/main.py`:

- **Products:** `GET /api/products`, `GET /api/products/{id}`, `GET /api/products/search`, `GET /api/products/compare`
- **Cart:** `POST /api/cart`, `GET /api/cart/{id}`, `POST /api/cart/{id}/items`, `DELETE /api/cart/{id}/items/{item_id}`
- **Orders:** `POST /api/orders`, `GET /api/orders`, `GET /api/orders/{id}`, `GET /api/orders/{id}/decision-replay`
- **Payments:** `POST /api/payments/create`, `POST /api/payments/verify`, `GET /api/payments/{order_id}`
- **Policies:** `GET /api/policies`, `PUT /api/policies`, `POST /api/policies/simulate`
- **Audit:** `GET /api/audit`, `GET /api/audit/{id}`, `GET /api/audit/session/{session_id}`
- **Webhooks:** `POST /api/webhooks/razorpay`, `GET /api/webhooks`, `POST /api/webhooks/simulate`
- **AI Buyer API (v1):** `GET /api/agent/v1/tools`, `GET /api/agent/v1/catalog`, `POST /api/agent/v1/search`, `POST /api/agent/v1/cart`, `POST /api/agent/v1/checkout`, `GET /api/agent/v1/orders/{id}`
- **Human Approvals:** `GET /api/approvals`, `GET /api/approvals/{id}`, `POST /api/approvals/{id}/decide`
- **Agent Budget & Trust:** `GET /api/governance/budget`, `POST /api/governance/budget`, `GET /api/governance/trust`
- **Multi-Agent Registry:** `GET /api/agents`, `GET /api/agents/{id}`, `POST /api/agents/{id}/status`, `GET /api/agents/{id}/safety`
- **MCP Layer:** `GET /api/mcp/tools`, `POST /api/mcp/call`
- **A2A Commerce:** `POST /api/a2a/simulate`
- **Analytics & Growth:** `GET /api/analytics/revenue`, `POST /api/analytics/copilot`, `POST /api/campaigns/propose`, `POST /api/campaigns/{id}/activate`
- **Advanced Tools:** Support agent, dynamic pricing, cart optimizer, what-if simulator, live event stream, customer memory.

---

## 4. Existing Services

- `agent_registry_service.py`: Agent seed, permissions check, minute/hour/day velocity limits, circuit breaker tracking, kill switches.
- `approval_service.py`: 5-minute expiring human approvals, approval decision processing, validation before payment capture.
- `audit_service.py`: Creation and query of structured audit logs and agent tool action traces.
- `budget_service.py`: Per-transaction and daily remaining budget verification with daily auto-reset.
- `trust_service.py`: 0–100 behavioral trust scoring factoring success rate, violations, payment failures, and approvals.
- `policy_service.py`: Deterministic purchase limits, discount caps, risk classification (LOW/MEDIUM/HIGH), and explainability.
- `payment_service.py`: Razorpay client wrapper, test mode order creation, signature verification, payment failure handling.
- `order_service.py`: Multi-step order creation pipeline, idempotency verification, server-side price computation.
- `recommendation_service.py`: Cross-sell and upsell scoring, event telemetry tracking.
- `analytics_service.py`: Store revenue, conversion attribution, AI copilot responses.
- `prompt_security_service.py`: Regex-based prompt injection detection.
- `safety_certification_service.py`: 10-point automated sandbox safety test suite.

---

## 5. Existing Frontend Routes

The Next.js frontend has 26 verified routes:
- `/` (Home & Overview)
- `/shop` (Conversational AI Shop & Negotiation)
- `/agents` (Multi-Agent Registry & Controls)
- `/agents/[id]/safety` (Safety Certification Audit)
- `/ai-buyer` (AI Buyer & A2A Simulator)
- `/analytics` (Merchant Intelligence)
- `/audit` (Audit Log Viewer)
- `/dashboard` (Merchant Dashboard)
- `/decisions` (Decision Replay V1)
- `/developers` & `/developers/playground` (API Keys & Testing)
- `/growth` (Campaigns & A/B Experiments)
- `/live` (Real-Time Telemetry Stream)
- `/orders` & `/orders/[id]` (Order Management)
- `/policies/simulator` (Policy Simulator)
- `/pricing` (Dynamic Pricing Simulator)
- `/products` (Catalog Management)
- `/security` (Security Lab — 15 Scenarios)
- `/settings` (Store & Governance Settings)
- `/simulator` (What-If Business Simulator)
- `/support` (Customer Support Agent & Refunds)
- `/trust` (Trust & Governance Center)
- `/webhooks` (Webhook Event Monitor)

---

## 6. Existing Tests & Verification Results

- **Backend Pytest:** Executed `.\venv\Scripts\python -m pytest` in `backend/`.
  - **Result:** **34 passed, 0 failed** in 2.38s.
- **Frontend Build:** Executed `npm run build` in `frontend/`.
  - **Result:** **26 routes compiled and optimized successfully** with zero TypeScript errors.

---

## 7. Identified Gaps & Upgrade Roadmap

While the foundation is solid, the following areas require upgrades to meet the production-quality agentic commerce specification:

| Area | Current State | Required Upgrade |
| :--- | :--- | :--- |
| **Agent Identity System** | Static default agents in DB with simple hash | Comprehensive Admin API (`POST /api/admin/agents`, `GET /api/admin/agents`, `GET /api/admin/agents/{id}`, `PATCH /api/admin/agents/{id}`, `POST /api/admin/agents/{id}/rotate-key`, `POST /api/admin/agents/{id}/pause`, `POST /api/admin/agents/{id}/resume`) with secure API key generation and raw key masking. |
| **Agent Permissions** | Basic list of coarse permissions | 16 fine-grained permissions (`catalog.read`, `product.search`, `cart.write`, `checkout.request`, `approval.request`, etc.), middleware authentication, structured permission-denied errors and audit events. |
| **Global Kill Switch** | Per-agent kill switch only | System-wide controls (`global_write_enabled`, `payments_enabled`, `campaigns_enabled`, `agent_execution_enabled`) via `/api/admin/system/*` with immediate financial gating. |
| **Velocity Limiter** | Embedded in budget service | Dedicated `VelocityLimiter` service with Redis + DB fallback, structured responses (`ALLOWED`, `RATE_LIMITED`, `VELOCITY_LIMIT_EXCEEDED`), and audit logs. |
| **Circuit Breaker** | Basic failure count flag | Full state machine (`CLOSED`, `OPEN`, `HALF_OPEN`) with cooldown timer, half-open test count, API status endpoint, and circuit transition audits. |
| **Dynamic Risk Score** | Fixed level bucket scores | Continuous `0-100` numeric risk scoring factoring amount, agent trust, velocity, payment failures, discount anomalies, and budget utilization with explicit reason codes. |
| **Dynamic Trust Score** | Point addition/subtraction | Weighted deterministic signals with positive/negative factor breakdown, reason codes, and dynamic spending limit tier mapping. |
| **Dynamic Spending Limits** | Fixed limits per agent | Trust-driven tiers (Trust 90-100 → ₹10,000; 70-89 → ₹5,000; 50-69 → ₹2,000; <50 → human approval mandatory) configurable via policy. |
| **Human Approval System** | Basic decide endpoint | Upgraded server-side approval model with `GET /api/admin/approvals`, `GET /api/admin/approvals/{id}`, `POST /api/admin/approvals/{id}/approve`, `POST /api/admin/approvals/{id}/reject`. |
| **Order State Machine** | 8 basic states | Complete 12-state deterministic state machine with strict transition validation, rejection of invalid transitions, and transition audit events. |
| **Payment Idempotency** | Basic key check | Strict idempotency middleware: same key + same payload = cached result; same key + different payload = `409 Conflict`. |
| **Webhook Security** | Signature check & duplicate set | Enhanced HMAC verification, full payload correlation, idempotent transitions, structured failure recovery. |
| **Tamper-Evident Audit Trail** | Standard relational logs | Cryptographic hash chaining (`previous_hash` + `event_hash` SHA-256) with `GET /api/admin/audit/verify` integrity validator. |
| **Request Correlation** | Partially present | Uniform `request_id`, `session_id`, `agent_id`, `tool_call_id`, `order_id`, `payment_id` propagation in headers, logs, and audits. |
| **Decision Replay V2** | 12-stage UI view | Structured decision metadata across all 15 stages without exposing raw hidden chain-of-thought. |
| **Multi-Agent Orchestration** | Pre-seeded agents | Enforced role-based capability boundaries (Shopping, Growth, Risk, Payment, Support, Supervisor) with non-overlapping privileges. |
| **Agent-to-Agent (A2A)** | Simulated flow | Explicit demo REST endpoints: `POST /api/a2a/discovery`, `POST /api/a2a/request`, `POST /api/a2a/offer`, `POST /api/a2a/accept`, `POST /api/a2a/reject`. |
| **MCP Improvements** | Basic tools wrapper | 16 clean tools with schema validation, agent auth, permission checks, policy checks, budget checks, and audit logging. |
| **Agent Manifest** | Not present | Machine-readable `/.well-known/agent.json` exposing capabilities, auth type, and governance guarantees. |
| **Python Agent SDK** | Not present | Lightweight `sdk/agentpay/` client with `examples/basic_agent.py` and `examples/checkout_agent.py`. |
| **Merchant Policy Builder** | Basic settings page | Frontend route `/settings/policies` with full backend persistence for caps, thresholds, velocity, and action matrices. |
| **Policy Simulator** | Basic simulator | Deterministic simulator on `/policy-simulator` returning permission, policy, risk, budget, trust, approval, and reason codes. |
| **Agent Management Dashboard** | View-only cards | Full `/agents` and `/agents/[id]` with metrics, permissions, key rotation, circuit breaker state, and audit timeline. |
| **Live Activity Stream** | Telemetry cards | Real-time event stream on `/activity` (polling/SSE fallback). |
| **Agent Health Dashboard** | Basic safety score | Metrics on `/health/agents` for success rate, blocked rate, latency, failures, violations, circuit breaker state. |
| **Revenue Attribution** | Basic summary | Breakdown of AI-generated vs AI-assisted vs organic vs upsell vs campaign revenue with full funnel conversion tracking. |
| **Security / Failure Lab V2** | 15 scenarios | Attack -> Defense -> Result -> Audit Event visualization with Chaos simulation controls. |
| **Admin Roles (RBAC)** | Single role | `OWNER`, `ADMIN`, `OPERATOR`, `ANALYST`, `VIEWER` demo-safe RBAC. |
| **Notification Center** | Not present | Frontend route `/notifications` with severity filters and mark-as-read controls. |
| **Observability & Health** | Basic `/health` | Structured logging without secrets, `/health/ready`, `/health/live`. |
| **Automated Tests** | 34 tests passing | Add comprehensive tests for all new modules (targeting 50+ total tests, 100% pass). |
| **Documentation** | Existing docs | Full suite: `docs/AGENT_SECURITY.md`, `docs/API.md`, `docs/AGENT_GUIDE.md`, `docs/THREAT_MODEL.md`, `docs/DECISION_REPLAY.md`, `docs/DEMO_SCENARIOS.md`, updated `ARCHITECTURE.md`, `README.md`, `DEMO.md`. |

---
