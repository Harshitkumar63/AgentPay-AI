# 🎬 AgentPay AI — Buildathon Judging & Demo Guide (3-5 Minutes)

> **Track:** AI Growth & Agentic Commerce  
> **Platform:** AgentPay AI — AI-Powered Agentic Commerce Engine for Modern Merchants

---

## 🎯 Demo Goal
Demonstrate how **AgentPay AI** transforms a traditional catalog into an **AI-transactable storefront** while maintaining strict **financial guardrails**, **risk gating**, **human-in-the-loop approvals**, and **seamless Razorpay checkout**.

---

## ⏱️ Step-by-Step Presentation Script

### 1. Merchant Dashboard Overview (30 Seconds)
- **Navigate to:** `http://localhost:3000/dashboard`
- **Key Points to Highlight:**
  - Real-time aggregated store performance: **Total Revenue**, **Orders**, **Average Order Value (AOV)**, and **AI-Assisted Revenue**.
  - Conservative revenue attribution separating direct purchases from AI-assisted conversions.
  - Active payment health indicator showing Razorpay Test Mode.

---

### 2. Natural Language Product Discovery & Algorithmic Upselling (60 Seconds)
- **Navigate to:** `http://localhost:3000/shop`
- **Action:**
  - Click the quick prompt pill: `"Find black running shoes under ₹3000"` or type it in the chat box.
- **What to Highlight:**
  - **Zero Hallucination Guarantee:** The agent executes `search_products(query="running shoes", color="black", max_price=3000)` against the SQLite database.
  - Notice the **"Why did the AI do this?"** decision explanation widget showing verified budget fit, category match, and live inventory status.
  - Notice the cross-sell recommendation: *"Performance Running Socks (3-Pack)"* dynamically suggested.
  - Click **Add to Cart** on `ProRunner X1 Running Shoes`.

---

### 3. Gated Checkout & Human-in-the-Loop Approval Gate (60 Seconds)
- **Action:**
  - Type or click: `"Buy now"` or click **Gated AI Checkout** in the cart sidebar.
- **What Happens Behind the Scenes:**
  1. Re-verifies live inventory from the database.
  2. Server-side price recalculation (never trusts frontend client amounts).
  3. **Policy Engine Check:** Compares amount against merchant maximum limit (₹50,000) and discount cap (20%).
  4. **Risk Engine Assessment:** Classifies the order as `HIGH RISK` because it commits financial funds.
- **What Appears on Screen:**
  - The **Human Approval Gate Modal** pops up with calculated totals, policy decision (`ALLOWED`), and risk classification (`HIGH RISK`).
- **Action:**
  - Click **"Confirm Purchase"**.
  - Notice the instantaneous transition to Razorpay Test Mode checkout, verification of cryptographic signature, and immediate order fulfillment.

---

### 4. Agent Execution Trace & Immutable Audit Trail (45 Seconds)
- **Navigate to:** `http://localhost:3000/agent`
  - Show the step-by-step tool execution pipeline: `search_products()` → `add_to_cart()` → `create_order()` → `get_payment_status()`.
  - Expand any step to inspect the exact input arguments, execution duration in milliseconds, and structured JSON output.
- **Navigate to:** `http://localhost:3000/audit`
  - Show the cryptographic audit log entry for the purchase: Actor (`ai_agent`), Action (`CREATE_ORDER`), Policy Result (`ALLOWED`), Approval Status (`APPROVED`), Result (`SUCCESS`).

---

### 5. Webhook Event Monitor & Idempotency Proof (45 Seconds)
- **Navigate to:** `http://localhost:3000/webhooks`
  - Show the live gateway webhook events log (`payment.captured`, `payment.authorized`).
  - **Live Demonstration:** Click **"Simulate payment.captured"** button.
  - Click it a second time with the same event: Notice the status changes to `Idempotent Ignored` (`already_processed`), proving that network retries and replay attacks cannot cause double charges.

---

### 6. Security & Failure Demonstration Lab (45 Seconds)
- **Navigate to:** `http://localhost:3000/security`
  - Click **"Run Test"** on **Scenario 1 (Purchase Limit Breach)**:
    - AI attempts a ₹75,000 transaction exceeding the ₹50,000 policy limit → **BLOCKED** with audit logging.
  - Click **"Run Test"** on **Scenario 2 (Excessive Discount Injection)**:
    - Attempting a 40% discount override → **BLOCKED** by policy cap.
  - Click **"Run Test"** on **Scenario 5 (Gateway Payment Failure Recovery)**:
    - Simulates payment decline → safely logged as `PAYMENT_FAILED` without corrupting order state.

---

### 7. AI Growth Center & Merchant AI Copilot (30 Seconds)
- **Navigate to:** `http://localhost:3000/growth`
  - Show the clear distinction between **Actual Captured Revenue** vs. **Estimated Growth Opportunity**.
  - In the **Merchant AI Copilot**, click: `"Why did revenue change this month?"` or `"What products should I promote?"`.
  - Copilot responds with database-grounded insights and generates an **AI Campaign Proposal** with explicit merchant approval gating.

---

## 🏆 Key Takeaways for Judges
1. **Safety First:** The LLM NEVER has direct access to Razorpay APIs or raw payment execution.
2. **Zero Hallucinations:** All pricing, stock, and recommendations are anchored in backend services.
3. **Idempotency & Integrity:** Replay attacks, duplicate orders, and gateway failures are handled safely and logged immutably.
4. **Machine-to-Machine Ready:** External autonomous AI agents can discover and purchase via `/api/agent/v1/...` AI Buyer API.
