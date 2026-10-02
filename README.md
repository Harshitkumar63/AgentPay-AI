# 🤖 AgentPay AI — Governed Agentic Commerce, FinTech & Payment Gateway

> **Razorpay Buildathon Track:** AI Growth & Agentic Commerce  
> **Tagline:** AI-Powered Agentic Commerce, Algorithmic Growth & Deterministic Governance for Modern Merchants

---

## 🌟 1. Executive Summary & Problem Statement

### The Problem
As autonomous AI agents, personal assistants, and chatbots become the primary interface for online discovery, traditional eCommerce platforms face major security and governance vulnerabilities:
1. **Unsafe LLM Autonomy**: Allowing generative AI to initiate purchases or touch payment gateways directly risks hallucinated orders, rogue discounts, and financial leaks.
2. **Opaque Pricing & Stock**: AI agents can fabricate non-existent products, prices, and promotional codes unless bounded by a strict, authoritative database service layer.
3. **Missing Machine Governance**: Merchants lack granular policy limits (purchase caps, discount limits, multi-agent permissions, velocity limits, circuit breakers, trust scoring, and human-in-the-loop approvals) designed specifically for machine-initiated commerce.

### The Solution: AgentPay AI
**AgentPay AI** bridges autonomous AI agents and **Razorpay's Payment Infrastructure** through an authoritative **Defense-in-Depth Architecture**. It enables conversational discovery, algorithmic upselling/cross-selling, controlled price negotiations, dynamic pricing simulations, inventory intelligence, and machine-to-machine commerce, while ensuring every financial commitment is strictly gated by merchant policies, continuous 0-100 risk classification, dynamic agent budgets & trust scoring, human approvals with 5-minute TTL, and cryptographic tamper-evident SHA-256 audit trails.

---

## 🎯 2. Complete Capabilities & Feature Grid

| Capability Area | Route / API | Implementation Highlights |
| :--- | :--- | :--- |
| **Multi-Agent Registry & Key Vault** | `/agents`, `/agents/[id]`, `/api/admin/agents` | Scoped tool permissions, SHA-256 key hashing, key rotation, velocity counters, 3-state circuit breakers, emergency kill switches. |
| **Global Emergency Kill Switch** | `/api/admin/system/*` | Fine-grained global write freeze, payment freeze, agent freeze, and campaign freeze with instant activation. |
| **Tamper-Evident Audit Trail** | `/audit`, `/api/admin/audit/verify` | SHA-256 cryptographic hash-chained log from Genesis with mathematical tamper detection. |
| **Controlled Price Negotiation** | `/shop`, `/api/negotiation` | Bounded counter-offers enforcing merchant discount caps and minimum margin policies. |
| **Dynamic Pricing Simulator** | `/pricing`, `/api/pricing` | Demand elasticity and inventory velocity modeling without mutating active database catalog prices. |
| **Inventory Risk Intelligence** | `/inventory`, `/api/inventory` | Real-time stockout risk, overstock risk, days remaining, and replenishment proposals. |
| **Cart Optimizer Engine** | `/shop`, `/api/cart-optimizer` | 4 optimization modes (`MINIMUM_PRICE`, `BEST_VALUE`, `BEST_QUALITY`, `MAXIMUM_SAVING`) with live item replacement diffs. |
| **What-If Business Simulator** | `/simulator`, `/api/simulator` | Hypothetical forecasting for promotional discounts, inventory expansion, and catalog price shifts. |
| **AI A/B Testing** | `/growth`, `/api/experiments` | Multi-variant pricing tests tracking views, orders, conversion lifts, and automated recommendations. |
| **Managed Refund Workflow** | `/support`, `/api/refunds` | Gated refund state machine (`REQUESTED` → `APPROVAL_PENDING` → `APPROVED` → `COMPLETED`). |
| **Customer Support Agent** | `/support`, `/api/support` | Zero-hallucination support grounded strictly in verified PostgreSQL/SQLite order and payment records. |
| **Agent-to-Agent (A2A) Commerce** | `/ai-buyer`, `/api/a2a/*` | Complete REST machine-to-machine interaction (`discovery`, `request`, `offer`, `accept`, `reject`). |
| **Model Context Protocol (MCP)** | `/api/mcp/tools`, `/api/mcp/call` | 16 clean tools with schema validation, permission checks, and audit logging. |
| **Official Python Agent SDK** | `sdk/agentpay/` | Lightweight Python client with examples for discovery, cart management, and governed checkout. |
| **Machine-Readable Manifest** | `/.well-known/agent.json` | Public machine-readable capabilities without exposing secrets. |
| **Security Alerts Center** | `/notifications`, `/api/notifications` | Real-time alert feed for approval requests, policy violations, budget alerts, and circuit breaker trips. |
| **Decision Replay (15 Stages)** | `/decisions`, `/api/agent/v1/decisions` | 15-stage structured reconstruction of the exact governance path from intent to capture. |
| **Live Event Stream & Telemetry** | `/live`, `/api/live` | Real-time agent event stream, response latency, payment gateway latency, and revenue attribution. |

---

## 🏛️ 3. Authoritative Defense-in-Depth Pipeline

```
[Untrusted User / External AI Agent]
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 1: Agent Key Authentication & Context Correlation     │
│  (X-Agent-Key SHA-256 verify, X-Request-ID, X-Session-ID)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 2: Global Kill Switch & Scoped Tool Permissions       │
│  (Validates granted capabilities & role-based access)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 3: 3-State Circuit Breaker & Velocity Limiter         │
│  (Trips on 5 declines in 2m; Rate limit 60 req/m, 5 tx/m)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 4: Authoritative Server-Side Price Recomputation      │
│  (Client amounts ignored, verified from DB catalog)         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 5: Continuous 0-100 Risk Engine Scoring               │
│  (LOW, MEDIUM, HIGH, CRITICAL with explicit Reason Codes)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 6: Dynamic Agent Budget & Trust Spending Tiers        │
│  (Trust 90-100: ₹10k, 70-89: ₹5k, 50-69: ₹2k, <50: Gate)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 7: Human-in-the-Loop Approval Gate                    │
│  (5-minute expiring authorization TTL on high-risk actions) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Gate 8: 12-State Deterministic Order Machine & Razorpay    │
│  (Strict legal transitions, Idempotency conflict guard)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       Authoritative Database       Tamper-Evident Audit Trail
                                   (SHA-256 Hash Chain from Genesis)
```

> [!IMPORTANT]
> **Cardinal Rule:** The LLM NEVER touches Razorpay credentials, bank accounts, or financial balance mutations directly. The LLM suggests intent, but compiled Python backend code authoritatively verifies policy, risk, price, and payment execution.

---

## 🛠️ 4. Tech Stack

- **Backend:** FastAPI (Python 3.11+ / 3.14), SQLAlchemy ORM, Pydantic V2, SQLite / PostgreSQL.
- **Frontend:** Next.js 16 (Turbopack, App Router), React 19, TypeScript, Vanilla CSS Design System, Lucide Icons (27 routes).
- **Payment Gateway:** Razorpay Standard Checkout & Orders API (Test Mode), HMAC-SHA256 Signature Verification.
- **AI Integrations:** OpenAI Function Calling (`gpt-4o`), Google Gemini (`gemini-1.5-pro`), and Zero-Config Deterministic Fallback.
- **Protocol Standards:** Model Context Protocol (MCP) Compatible Tools Layer (`/api/mcp/tools`, `/api/mcp/call`).
- **Testing:** Pytest (**52 automated unit & integration tests with 100% pass rate**).

---

## 🚀 5. Quickstart & Running Locally

### Prerequisites
- Python 3.11+ (or 3.12 / 3.14)
- Node.js 18+ / 20+

### Step 1: Backend Setup
```bash
cd backend

# Create & activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend server
uvicorn app.main:app --reload --port 8000
```
Backend API live at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs`.

### Step 2: Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Frontend dashboard live at `http://localhost:3000`.

### Step 3: Run Backend Tests
```bash
cd backend
.\venv\Scripts\python -m pytest
```
All **52 tests** will execute and validate the complete governance and commerce engine.

---

## 📚 6. Documentation Index

- [Agent Security Model](docs/AGENT_SECURITY.md)
- [Complete REST & MCP API Reference](docs/API.md)
- [Agent Developer Guide & Python SDK](docs/AGENT_GUIDE.md)
- [Threat Model & Security Invariants](docs/THREAT_MODEL.md)
- [Decision Replay Specification](docs/DECISION_REPLAY.md)
- [Demo Walkthrough & Presentation Scenarios](docs/DEMO_SCENARIOS.md)
- [Implementation Audit](docs/IMPLEMENTATION_AUDIT.md)
