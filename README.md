# 🤖 AgentPay AI — Autonomous Agentic Commerce & Governance Platform

> **Razorpay Buildathon Track:** AI Growth & Agentic Commerce  
> **Tagline:** AI-Powered Agentic Commerce, Algorithmic Growth & Deterministic Governance for Modern Merchants

---

## 🌟 1. Executive Summary & Problem Statement

### The Problem
As autonomous AI agents, personal assistants, and chatbots become the primary interface for online discovery, traditional eCommerce platforms face major security and governance vulnerabilities:
1. **Unsafe LLM Autonomy**: Allowing generative AI to initiate purchases or touch payment gateways directly risks hallucinated orders, rogue discounts, and financial leaks.
2. **Opaque Pricing & Stock**: AI agents can fabricate non-existent products, prices, and promotional codes unless bounded by a strict, authoritative database service layer.
3. **Missing Machine Governance**: Merchants lack granular policy limits (purchase caps, discount limits, agent spending budgets, trust scoring, and human-in-the-loop approvals) designed specifically for machine-initiated commerce.

### The Solution: AgentPay AI
**AgentPay AI** bridges autonomous AI agents and **Razorpay's Payment Infrastructure** through a **4-Layer Defense-in-Depth Architecture**. It enables conversational discovery, algorithmic upselling/cross-selling, and machine-to-machine commerce, while ensuring every financial commitment is strictly gated by merchant policies, risk classification, agent budgets, trust scoring, human approvals with 5-minute TTL, and cryptographic audit trails.

---

## 🎯 2. How AgentPay AI Solves the Razorpay Buildathon Track

| Buildathon Theme Requirement | How AgentPay AI Implements & Solves It |
| :--- | :--- |
| **AI-Powered Shopping & Discovery** | Multi-turn conversational shopping agent with tokenized catalog search, price budgets, and color memory across turns. |
| **AI-Readable Merchant Catalog** | Dedicated machine-to-machine **AI Buyer API (`/api/agent/v1/...`)** exposing structured JSON catalog feeds & MCP tool specs. |
| **Upselling & Cross-Selling** | Algorithmic "Frequently Bought Together" cross-sells and tiered upsell recommendations with live conversion telemetry. |
| **Deterministic Policy & Risk Gating** | 3-tier risk engine (`LOW`, `MEDIUM`, `HIGH`) and configurable merchant policies (max amount, max discount, action whitelists). |
| **Agent Budget & Trust Governance** | Server-calculated **Agent Trust Score (0–100)**, per-transaction spending limits, and daily remaining capacity. |
| **Human-in-the-Loop Approval Gate** | High-risk financial operations pause and require interactive human confirmation (with 5-minute TTL) before Razorpay order dispatch. |
| **Razorpay Test Mode & Webhooks** | Server-to-server Razorpay order creation, HMAC-SHA256 signature verification, and idempotent webhook processing. |
| **Decision Replay & Observability** | 16-stage **Agent Execution Trace** (`/agent`) and full **Decision Replay** (`/orders/{id}`) reconstructing the exact decision journey. |
| **Merchant AI Copilot & Growth** | Merchant assistant (`/growth`) analyzing revenue drop causes, stock velocity, and proposing campaign orchestrations. |
| **Security & Failure Lab** | Interactive testing sandbox (`/security`) demonstrating all 10 security scenarios, purchase limit blocks, discount caps, idempotency, and gateway failure recovery. |

---

## 🏛️ 3. Defense-in-Depth Safety Architecture

```
User / External AI Agent
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: AI Agent / AI Buyer API (Intent & Tool Selection) │
│  (18 Dedicated Commerce Tools • 16-Stage Execution Trace)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Structured Tool Invocation
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Policy & Risk Engine (Deterministic Governance)   │
│  (Max Purchase Caps, Discount Limits, Risk Scoring: Low/Med/High)│
└──────────────────────────────┬──────────────────────────────┘
                               │ Policy Passed + Risk Classified
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Agent Budget, Trust Score & Human Approval Gate   │
│  (Per-Tx Limits, Daily Budget, Trust Score, 5m Approval TTL) │
└──────────────────────────────┬──────────────────────────────┘
                               │ Authorized & Verified
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Payment Service & Razorpay Gateway                │
│  (Server-Side Price Recomputation, HMAC Signature, Webhook) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
       SQLite / PostgreSQL            Immutable Audit Trail
```

> [!IMPORTANT]
> **Cardinal Security Rule:** The LLM NEVER touches Razorpay credentials or unrestricted payment APIs. The LLM decides *WHAT* tool to use, but the deterministic backend enforces *WHETHER* the action is permitted.

---

## 🛠️ 4. Tech Stack

- **Backend:** FastAPI (Python 3.11+ / 3.14), SQLAlchemy ORM, Pydantic V2, SQLite / PostgreSQL.
- **Frontend:** Next.js 16 (Turbopack, App Router), React 19, TypeScript, Vanilla CSS Design System, Lucide Icons.
- **Payment Gateway:** Razorpay Standard Checkout & Orders API (Test Mode), HMAC-SHA256 Signature Verification.
- **AI Integrations:** OpenAI Function Calling (`gpt-4o`), Google Gemini (`gemini-1.5-pro`), and Zero-Config Deterministic Fallback.
- **Protocol Standards:** Model Context Protocol (MCP) Compatible Tools Layer (`/api/mcp/tools`, `/api/mcp/call`).
- **Testing & Tooling:** Pytest (23 automated tests), TestClient, Docker Compose.

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
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated tests (23 tests)
pytest -v

# Start FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Docs:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

### Step 2: Frontend Setup
```bash
cd frontend

# Install packages
npm install

# Build for production validation
npm run build

# Start Next.js dev server
npm run dev
```
- **Web App:** `http://localhost:3000`

---

## 🐳 6. Running with Docker Compose

Run the entire full-stack application with a single command:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## 💳 7. Razorpay Test Mode Configuration

To test with real Razorpay test keys:
1. Edit `backend/.env`:
   ```env
   RAZORPAY_KEY_ID=rzp_test_YourKeyIdHere
   RAZORPAY_KEY_SECRET=YourKeySecretHere
   RAZORPAY_WEBHOOK_SECRET=YourWebhookSecretHere
   DEMO_MODE=false
   ```
2. If keys are omitted, the application operates in **Deterministic Zero-Config Demo Mode**, simulating all gateway handshakes, signatures, and webhooks with audit logging.

---

## 🤖 8. AI Buyer API (v1) for Autonomous Agents

External AI agents (such as MCP agents, Claude, or LangChain agents) can transact directly via REST:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/agent/v1/tools` | `GET` | Machine-readable MCP / OpenAI tool definitions. |
| `/api/agent/v1/catalog` | `GET` | Machine-readable catalog feed formatted for LLM consumption. |
| `/api/agent/v1/catalog/{id}` | `GET` | Factual product specifications & live stock status. |
| `/api/agent/v1/search` | `POST` | Natural language catalog query endpoint. |
| `/api/agent/v1/cart` | `POST` | Create or initialize an agent cart session. |
| `/api/agent/v1/cart/{id}/items`| `POST` | Add item with server-side price validation. |
| `/api/agent/v1/checkout` | `POST` | Execute policy-gated checkout with risk assessment. |
| `/api/agent/v1/orders/{id}` | `GET` | Retrieve order status & receipt. |
| `/api/agent/v1/payments/{id}`| `GET` | Query verified payment state. |
| `/api/mcp/tools` | `GET` | Model Context Protocol compatible tool registry. |
| `/api/mcp/call` | `POST` | Direct tool invocation via MCP interface. |

---

## 🧪 9. Automated Test Suite (23 Tests)

Run the full automated test suite:
```bash
cd backend
pytest -v
```

### Test Coverage:
1. `test_product_search_and_filters`: Tokenized search, color matching, price budgets.
2. `test_recommendation_scoring_and_generation`: Multi-factor deterministic scoring and relations.
3. `test_inventory_check_insufficient`: Stock exhaustion checks prevent overselling.
4. `test_cart_operations_and_calculations`: Subtotal, quantity, and server-side pricing recalculation.
5. `test_policy_engine_limits_and_discounts`: Transaction value caps and discount percentage limits.
6. `test_agent_budget_limits`: Transaction caps and daily remaining capacity enforcement.
7. `test_agent_trust_score_calculation`: Dynamic score calculation based on violations and success rate.
8. `test_human_approval_lifecycle_and_expiration`: Human approval authorization and 5-minute TTL.
9. `test_expired_approval_rejection`: Stale authorization token rejection.
10. `test_idempotency_order_creation`: Same idempotency key returns existing order without duplicates.
11. `test_duplicate_webhook_protection`: Replay attacks on webhook event IDs safely ignored.
12. `test_payment_failure_handling`: Gateway declines recorded safely with audit trails.
13. `test_product_comparison`: Side-by-side feature, pro/con, and suitability scoring.
14. `test_ai_buyer_api_endpoints`: End-to-end machine-to-machine commerce API.
15. `test_merchant_ai_copilot`: Analytics-grounded copilot Q&A.
16. `test_campaign_proposal_and_activation`: AI campaign proposal creation and merchant activation.
17. `test_decision_replay_endpoint`: Complete 16-stage journey reconstruction.
18. `test_mcp_endpoints`: Model Context Protocol schema and execution.
19. `test_end_to_end_commerce_pipeline`: Full integration test from user request to webhook & audit ledger.
20. `test_max_tool_call_limit`: Safety limit enforcing max 8 tool calls.
21. `test_price_tamper_resistance`: Server-side recalculation ignores client price tampering.
22. `test_policy_simulator_endpoint`: Interactive policy simulator compliance check.
23. `test_recommendation_event_telemetry`: Recommendation lifecycle event logging and analytics.

---

## 📄 10. Buildathon Live Demo Script

Follow our 3-5 minute live demonstration walkthrough in [`DEMO.md`](file:///c:/Users/harsh/Desktop/RAZOR%20PAY/DEMO.md) and full architecture specs in [`docs/ARCHITECTURE.md`](file:///c:/Users/harsh/Desktop/RAZOR%20PAY/docs/ARCHITECTURE.md).
