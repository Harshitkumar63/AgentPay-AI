# 🤖 AgentPay AI — AI-Powered Agentic Commerce Platform

> **Razorpay Buildathon Track:** AI Growth & Agentic Commerce  
> **Subtitle:** AI-Powered Agentic Commerce for Modern Merchants  

---

## 🌟 Executive Summary

**AgentPay AI** is a production-grade, secure, autonomous agentic commerce platform that makes modern merchants transactable by AI agents and turns natural language shopping queries into safe, policy-governed Razorpay transactions.

### Key Capabilities:
- **AI-Readable Merchant Catalog**: Real-time product feeds and search endpoints optimized for LLM tool-calling and autonomous AI buyers.
- **AI Shopping Assistant**: Natural language product discovery, intelligent cross-selling, upsells, cart management, and multi-step reasoning.
- **Policy-Based Financial Guardrails**: Configurable merchant limits (max purchase amounts, discount caps, action whitelists) strictly verified in backend services.
- **Human-in-the-Loop Financial Gating**: High-stakes financial actions require explicit user approval before payment orders are created.
- **Full Razorpay Test-Mode Integration**: Server-to-server Razorpay Order creation, frontend Standard Checkout integration, HMAC-SHA256 signature verification, and idempotent webhook handling.
- **Immutable Audit Trail & Governance**: Every agent tool execution, policy evaluation, user approval, and financial transaction is cryptographically tracked.
- **Merchant Revenue & Growth Analytics**: Automated AI revenue attribution, cross-sell/upsell effectiveness tracking, and growth recommendations.

---

## 🏛️ System Architecture

AgentPay AI implements a strict **4-Layer Defense-in-Depth Architecture** ensuring AI agents cannot perform unauthorized financial actions or bypass validation:

```
┌─────────────────────────────────────────────────────────────┐
│                 Layer 1: AI Agent & LLM                     │
│  (Natural Language Understanding, Intent Extraction, Tools) │
└──────────────────────────────┬──────────────────────────────┘
                               │ Structured Tool Invocation
                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Layer 2: Merchant Policy Engine                │
│ (Max Order Limits, Discount Guardrails, Action Whitelists)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Policy Evaluated (Pass / Block)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│         Layer 3: User Approval & Gating Layer               │
│ (Explicit Confirmation Dialog, Idempotency Token Management)│
└──────────────────────────────┬──────────────────────────────┘
                               │ Approved
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          Layer 4: Core Services & Razorpay API              │
│ (Inventory Lock, Razorpay Orders, HMAC Signature Check, DB) │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.11+ / 3.12+ / 3.14
- Node.js 18+ / 20+
- (Optional) Docker & Docker Compose

---

### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations and seed sample catalog
python -m app.db.seed

# Start FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at:
- **API Base:** `http://127.0.0.1:8000`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/health`

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Frontend will be available at `http://localhost:3000`.

---

### 3. Docker Compose (Full Stack)

To run the complete platform in isolated containers:

```bash
docker-compose up --build
```

---

## 💳 Razorpay Test Mode & Credentials

To enable live Razorpay test-mode transactions:
1. Open `backend/.env` (or set environment variables):
   ```env
   RAZORPAY_KEY_ID=rzp_test_YourKeyIdHere
   RAZORPAY_KEY_SECRET=YourKeySecretHere
   RAZORPAY_WEBHOOK_SECRET=YourWebhookSecretHere
   ```
2. In the absence of credentials, **AgentPay AI operates in Zero-Config Demo Mode**, simulating end-to-end Razorpay order creation, mock checkout, and signature verification with audit logs.

---

## 🤖 AI Provider Configuration

AgentPay AI supports multiple AI backends via its tool-calling abstraction:

```env
# Choose: openai, gemini, or leave blank for Built-in Intent Engine
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

# Or Google Gemini:
AI_PROVIDER=gemini
GOOGLE_API_KEY=AIza...
GEMINI_MODEL=gemini-1.5-flash
```

---

## 📂 Project Structure

```
RAZOR PAY/
├── backend/
│   ├── app/
│   │   ├── agents/           # LLM Providers, Prompts, Shopping & Growth Agents
│   │   ├── api/              # FastAPI Routers (Products, Cart, Orders, Payments, Webhooks, etc.)
│   │   ├── db/               # Database Engine, Session, & Seed Script
│   │   ├── models/           # SQLAlchemy Models (Products, Carts, Orders, Payments, Audits, Policies)
│   │   ├── schemas/          # Pydantic Schemas & Validations
│   │   ├── services/         # Business Logic, Policy Engine, Razorpay Integration
│   │   └── config.py         # Application Settings
│   ├── tests/                # Automated Pytest Suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── dashboard/        # Merchant Revenue & Growth Dashboard
│   │   ├── shop/             # AI Conversational Commerce & Checkout
│   │   ├── products/         # Catalog Management
│   │   ├── orders/           # Order Tracking & Payment Status
│   │   ├── analytics/        # Revenue Attribution & Growth Metrics
│   │   ├── audit/            # Full Audit Trail & Security Logs
│   │   ├── agent/            # Agent Reasoning Traces & Tool Calls
│   │   ├── settings/         # Policy Engine Configuration
│   │   └── globals.css       # Premium Dark-Mode Theme
│   ├── components/           # Reusable UI & Layout Components
│   ├── services/             # Frontend API Client
│   ├── types/                # TypeScript Definitions
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🧪 Testing & Verification

Run the automated backend test suite:

```bash
cd backend
python -m pytest tests/test_all.py -v
```

All 6 automated tests verify:
- Natural-language product discovery & tokenized search
- Cart creation, item calculation, & subtotal tax math
- Policy guardrails (order limit rejection, discount gating)
- Order creation pipeline with automated audit logging
- Razorpay payment creation and signature verification
- Cross-sell and upsell recommendation engine

---

## 🛡️ Security & Reliability Architecture

1. **Backend-Only Secrets**: Razorpay Key Secret and Webhook Secret are never exposed to client browsers or AI prompts.
2. **Deterministic Financial Logic**: Pricing math, discounts, tax calculations, and policy validations are performed purely in deterministic backend code, never in LLM prompts.
3. **Idempotent Webhooks & Orders**: Webhook events and order creations utilize unique idempotency keys to prevent duplicate captures.
4. **Audit Immutability**: All sensitive operations are logged with timestamps, actor IDs, policy results, and metadata.
