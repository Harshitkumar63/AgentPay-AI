# 🏗️ AgentPay AI — System Architecture Specification

## 1. Architectural Philosophy

AgentPay AI is architected around one fundamental security invariant:
> **"Never allow non-deterministic AI models to determine financial truth, mutate pricing, or directly trigger monetary disbursements."**

The platform decouples **Intent & Discovery (AI Layer)** from **Verification & Execution (Deterministic FinTech Layer)**.

---

## 2. Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Client & Presentation Layer                        │
│   Next.js 16 (Turbopack, App Router) • Vanilla CSS Design System       │
│   • /shop             • /agents           • /decisions    • /trust      │
│   • /pricing          • /simulator        • /support      • /live       │
│   • /security (15 Scenarios)              • /developers/playground      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTPS / REST / JSON / MCP
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application Gateway                      │
│   • Multi-Agent Registry Router           • Controlled Negotiation API  │
│   • Dynamic Pricing Simulator API         • Inventory Risk Agent API    │
│   • Human Approvals & Refund Router       • Decision Replay Engine      │
│   • AI Buyer API (v1) & MCP Router        • Webhook Ingestion Engine    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
         ┌───────────────────────────┴───────────────────────────┐
         ▼                                                       ▼
┌───────────────────────────────────────┐       ┌───────────────────────────────────────┐
│       AI & Autonomous Layer           │       │    Deterministic Governance Core      │
│ • Natural Language Discovery Agent    │       │ • Tool Permission Boundary Matrix     │
│ • AI Negotiation Strategy Agent       │       │ • Kill Switch & Status Controller     │
│ • Inventory Intelligence Analyzer     │       │ • Velocity Limiter (Min/Hour/Day)     │
│ • Dynamic Pricing Elasticity Modeler  │       │ • Policy Engine & Discount Cap        │
│ • Prompt Injection Defense Interceptor│       │ • Risk Scoring Engine (Low/Med/High)  │
│ • Customer Support Agent (DB Grounded)│       │ • Agent Budget & Trust Calculator     │
│ • MCP Tools Layer (OpenAI Function)   │       │ • Expiring Human Approval Gate (5m)   │
└───────────────────┬───────────────────┘       └───────────────────┬───────────────────┘
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Commerce & Settlement Core                        │
│   • Authoritative Server-Side Cart & Pricing Engine (Client prices ignored)│
│   • Order State Machine (CREATED → PENDING_APPROVAL → COMPLETED)       │
│   • Razorpay Test Mode & HMAC-SHA256 Signature Verification Service     │
│   • Idempotent Webhook Processing Store & Deduplication                 │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
┌───────────────────────────────────────┐   ┌───────────────────────────────────┐
│          Database Layer               │   │       Observability & Audit       │
│  PostgreSQL / SQLite (SQLAlchemy ORM) │   │ • Persistent Immutable Audit Logs │
│  • Products, Cart, Orders, Payments   │   │ • 12-Stage Decision Replay Store  │
│  • Agents, Budgets, Trust Scores      │   │ • Real-time Telemetry & Latency   │
│  • Customer Memory & A/B Experiments  │   │ • AI Cost & ROI Rate Tracker      │
└───────────────────────────────────────┘   └───────────────────────────────────┘
```

---

## 3. The 8-Stage Deterministic Governance Pipeline

Every transaction executed by any human or AI agent must traverse all 8 stages sequentially:

1. **Gate 1: Agent Registry & Permissions** — Validates agent identity, role, and explicitly granted permissions (`CATALOG_READ`, `CART_WRITE`, `ORDER_CREATE`, `PRICING_SIMULATE`).
2. **Gate 2: Kill Switch & Circuit Breaker** — Validates agent status is `ACTIVE`. If status is `PAUSED`, `DISABLED`, or circuit breaker tripped, execution halts instantly.
3. **Gate 3: Velocity Limiters** — Ensures agent transaction rates stay under 5 req/min, 20 req/hr, and 100 req/day.
4. **Gate 4: Deterministic Policy Check** — Evaluates purchase amount caps, maximum discount percentages, and action whitelists in compiled Python code.
5. **Gate 5: Risk Engine Scoring** — Evaluates transaction risk (`LOW`, `MEDIUM`, `HIGH`) based on order value and history.
6. **Gate 6: Budget & Trust Evaluation** — Validates single-transaction limits, daily remaining budget capacity, and server-calculated Trust Score (0–100).
7. **Gate 7: Human Approval Gating** — If risk is HIGH or amount exceeds policy threshold, a 5-minute expiring authorization record is created, pausing checkout until merchant approval.
8. **Gate 8: Server-Side Price Calculation & Razorpay Capture** — Client-submitted totals are ignored; prices are recalculated directly from database rows, signed with HMAC-SHA256, and sent to Razorpay.

---

## 4. Multi-Agent Role Model

| Agent Role | ID | Permissions | Budget Cap (Daily) | Per-Tx Cap | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Shopping** | `ShoppingBot` | `CATALOG_READ`, `PRODUCT_READ`, `CART_WRITE`, `ORDER_CREATE`, `PRICING_SIMULATE` | ₹10,000 | ₹5,000 | Product discovery, recommendation scoring, and bounded price negotiations. |
| **Payment** | `PaymentBot` | `PRODUCT_READ`, `ORDER_CREATE`, `PAYMENT_READ` | ₹50,000 | ₹25,000 | Validates policy, checks budgets, gates human approvals, and triggers Razorpay orders. |
| **Growth** | `GrowthBot` | `ANALYTICS_READ`, `INVENTORY_READ`, `CAMPAIGN_CREATE` | ₹5,000 | ₹2,000 | Analyzes store revenue, tracks cross-sell/upsell metrics, and proposes campaigns. |
| **Support** | `SupportBot` | `CATALOG_READ`, `PRODUCT_READ`, `SUPPORT_READ`, `REFUND_REQUEST` | ₹2,000 | ₹1,000 | Answers customer inquiries with zero hallucination grounded in database records. |
| **Security** | `SecurityBot` | `CATALOG_READ`, `ANALYTICS_READ` | ₹0 | ₹0 | Monitors velocity limits, circuit breaker health, and safety certification scores. |

---

## 5. Security & Isolation Boundaries

- **Database Air-Gap**: Payment secrets, Razorpay API credentials, and webhook signing secrets never leave server memory.
- **Client Price Immunity**: The client sends only `product_id` and `quantity`. Prices are always queried from database rows.
- **Deterministic Prompt Defense**: Regex pattern matching interceptors and system data delimiters prevent prompt injection from modifying backend execution logic.
