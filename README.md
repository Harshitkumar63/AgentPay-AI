# 🤖 AgentPay AI — Autonomous Agentic Commerce & Growth Engine

> **Razorpay Buildathon Track:** AI Growth & Agentic Commerce  
> **Tagline:** AI-Powered Agentic Commerce & Financial Guardrails for Modern Merchants

---

## 🌟 1. Executive Summary & Problem Statement

### The Problem
As autonomous AI agents, chatbots, and AI shopping assistants become the primary interface for online discovery, traditional eCommerce platforms face major challenges:
1. **Unsafe LLM Autonomy**: Allowing generative AI to initiate purchases or touch payment gateways directly risks hallucinated orders, rogue discounts, and catastrophic financial leaks.
2. **Opaque Pricing & Stock**: AI agents often invent product features, prices, and fake promotional codes when not grounded by strict service layers.
3. **Missing Financial Governance**: Merchants lack granular policy limits (purchase caps, discount limits, risk classification) designed specifically for machine-initiated commerce.

### The Solution: AgentPay AI
**AgentPay AI** bridges autonomous AI agents and **Razorpay's Payment Infrastructure** through a **4-Layer Defense-in-Depth Architecture**. It enables seamless natural language discovery, algorithmic upselling/cross-selling, and machine-to-machine commerce, while ensuring every financial commitment is strictly gated by merchant policies, risk classification, human approvals, and cryptographic audit trails.

---

## 🎯 2. How AgentPay AI Solves the Razorpay Buildathon Track

| Buildathon Theme Requirement | How AgentPay AI Implements & Solves It |
| :--- | :--- |
| **AI-Powered Shopping & Discovery** | Multi-turn conversational shopping agent with tokenized catalog search, price budgets, and color memory across turns. |
| **AI-Readable Merchant Catalog** | Dedicated machine-to-machine **AI Buyer API (`/api/agent/v1/...`)** exposing structured JSON catalog feeds & MCP tool specs. |
| **Upselling & Cross-Selling** | Algorithmic "Frequently Bought Together" cross-sells and tiered upsell recommendations with revenue attribution. |
| **Policy Engine & Risk Gating** | 3-tier risk engine (`LOW`, `MEDIUM`, `HIGH`) and configurable merchant policies (max amount, max discount, action whitelists). |
| **Human-in-the-Loop Approval Gate** | High-risk financial operations pause and require interactive human confirmation before Razorpay order dispatch. |
| **Razorpay Test Mode & Webhooks** | Server-to-server Razorpay order creation, HMAC-SHA256 signature verification, and idempotent webhook processing. |
| **Observability & Audit Trail** | Step-by-step **Agent Execution Trace** (`/agent`) and full immutable **Audit Logs** (`/audit`). |
| **Merchant AI Copilot & Growth** | Merchant assistant (`/growth`) analyzing revenue drop causes, stock velocity, and proposing campaign orchestrations. |
| **Security & Failure Lab** | Interactive testing sandbox (`/security`) demonstrating purchase limit blocks, discount caps, idempotency, and gateway failure recovery. |

---

## 🏛️ 3. Defense-in-Depth Safety Architecture

```
User / External AI Agent
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: AI Agent / AI Buyer API (Intent & Tool Selection) │
│  (Zero Hallucination: All factual data comes from DB)        │
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
│  Layer 3: Human Approval Gate (Mandatory for High-Risk)     │
│  (Explicit User Confirmation, Idempotency Token Management) │
└──────────────────────────────┬──────────────────────────────┘
                               │ User Confirmed
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
> **Cardinal Rule:** The LLM NEVER touches Razorpay APIs directly. The LLM decides *WHAT* tool to use, but the deterministic backend enforces *WHETHER* the action is permitted.

---

## 🛠️ 4. Tech Stack

- **Backend:** FastAPI (Python 3.11+ / 3.14), SQLAlchemy ORM, Pydantic V2, SQLite / PostgreSQL.
- **Frontend:** Next.js 16 (Turbopack, App Router), React 19, TypeScript, Vanilla CSS Design System, Lucide Icons.
- **Payment Gateway:** Razorpay Standard Checkout & Orders API (Test Mode), HMAC-SHA256 Signature Verification.
- **AI Integrations:** OpenAI Function Calling (`gpt-4o`), Google Gemini (`gemini-1.5-pro`), and Zero-Config Deterministic Demo Mode.
- **Testing & Tooling:** Pytest, TestClient, Docker Compose.

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

# Run automated tests
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

## 🤖 8. AI Provider Configuration

AgentPay AI supports OpenAI, Google Gemini, and a built-in deterministic intent engine:
```env
# OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Or Google Gemini
AI_PROVIDER=gemini
GOOGLE_API_KEY=AIza...
GEMINI_MODEL=gemini-1.5-pro
```

---

## 🤖 9. AI Buyer API (v1) for Autonomous Agents

External AI agents (such as MCP agents or LangChain agents) can transact directly without using the human UI:

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

---

## 🧪 10. Test Suite

Run the full automated test suite:
```bash
cd backend
pytest -v
```

### Test Coverage Summary:
- `test_product_search_and_filters`: Tokenized search, color matching, price budgets.
- `test_inventory_check_insufficient`: Stock exhaustion checks prevent overselling.
- `test_cart_operations_and_calculations`: Subtotal, quantity, and server-side pricing recalculation.
- `test_policy_engine_limits_and_discounts`: Transaction value caps and discount percentage limits.
- `test_idempotency_order_creation`: Same idempotency key returns existing order without duplicates.
- `test_duplicate_webhook_protection`: Replay attacks on webhook event IDs safely ignored.
- `test_payment_failure_handling`: Gateway declines recorded safely with audit trails.
- `test_product_comparison`: Side-by-side feature, pro/con, and suitability scoring.
- `test_ai_buyer_api_endpoints`: End-to-end machine-to-machine commerce API.
- `test_merchant_ai_copilot`: Analytics-grounded copilot Q&A.
- `test_policy_simulator_endpoint`: Real-time compliance simulator.

---

## 📄 11. Buildathon Live Demo Script

Follow our 3-5 minute live demonstration walkthrough in [`DEMO.md`](file:///c:/Users/harsh/Desktop/RAZOR%20PAY/DEMO.md).
