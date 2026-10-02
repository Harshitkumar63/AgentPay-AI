# 🎬 AgentPay AI — Live Demonstration Script & Judge Walkthrough

This script provides a structured, high-impact demonstration of the **AgentPay AI** platform covering all tracks: Agentic Commerce, Growth, FinTech, and AI Governance.

---

## ⏱️ Timeline Overview

| Timestamp | Section | Key Features Demonstrated |
| :--- | :--- | :--- |
| **0:00 - 0:45** | **1. Vision & Architecture** | Autonomous Agentic Commerce & Deterministic Governance |
| **0:45 - 1:45** | **2. AI Conversational Shop** | Catalog Discovery, Controlled Price Negotiation, Cart Optimizer, Human Gate |
| **1:45 - 2:30** | **3. Multi-Agent Governance & Kill Switch** | Agent Registry, Scoped Permissions, API Key Rotation, Circuit Breakers, Global Freeze |
| **2:30 - 3:15** | **4. AI Buyer & A2A Commerce** | 15-Stage Decision Pipeline & Machine-to-Machine Negotiation |
| **3:15 - 4:00** | **5. Growth, Pricing & What-If** | Dynamic Pricing Simulator, What-If Forecasting, AI A/B Testing |
| **4:00 - 4:30** | **6. Tamper-Evident Audit Verification** | Cryptographic SHA-256 Hash Chain from Genesis & Mathematical Verification |
| **4:30 - 5:00** | **7. Live Telemetry & Security Lab** | Decision Replay, Real-Time Alert Feed, 15 Security Lab Attack Scenarios |

---

## 🚀 Step-by-Step Presentation Guide

### 1. Vision & Architecture (0:00 - 0:45)
- **Goal**: Introduce why merchants need deterministic safety as autonomous AI agents begin shopping for humans.
- **Talking Point**:
  > *"Autonomous AI agents represent the biggest shift in commerce since mobile payments. But merchants cannot let LLMs touch bank APIs or hallucinate prices. AgentPay AI introduces an authoritative Defense-in-Depth pipeline that binds AI autonomy to Razorpay's payment infrastructure: 'AI proposes. Deterministic backend decides.'"*

---

### 2. AI Conversational Shop & Negotiation (0:45 - 1:45)
- **Navigate to**: `/shop`
- **Action**:
  1. Click quick prompt: `Find black running shoes under ₹3000`.
  2. Notice the instant catalog extraction, inventory badge, and **Score: 95/100** recommendation badge.
  3. Click **"Negotiate Price"** on *ProRunner X1 Running Shoes*.
  4. Enter a counter-offer (e.g. ₹2,200). Click **"Submit Proposal"**.
  5. Show the transparent breakdown: *Current Price, Requested Price, Maximum Allowed Discount (15%), Final Offer, Status: ACCEPTED*.
  6. Click **"Optimize Cart"** in the sidebar → select **"Best Value"** or **"Minimum Price"** → click **"Apply Optimization"**.
  7. Click **"Gated AI Checkout"** → review the **Human Approval & Governance Modal** (Policy: ALLOWED, Risk: HIGH, Budget: AVAILABLE, Trust: 90/100, 5-Min TTL).
  8. Click **"Confirm Purchase"** to trigger Razorpay Test Mode verification and complete checkout.

---

### 3. Multi-Agent Registry & Kill Switch Controls (1:45 - 2:30)
- **Navigate to**: `/agents`
- **Action**:
  1. Showcase the specialized agents: `ShoppingBot`, `PaymentBot`, `GrowthBot`, `SupportBot`, `SecurityBot`.
  2. Click into an agent's detail profile (`/agents/[id]`) to show scoped tool permissions and key prefix.
  3. Click **"Rotate API Key"** to generate a new hashed credential.
  4. Demonstrate the **Emergency Kill Switch**: click **"Emergency Pause"** on an agent to instantly halt its financial transaction capabilities while catalog discovery stays active.

---

### 4. AI Buyer Simulator & Agent-to-Agent Commerce (2:30 - 3:15)
- **Navigate to**: `/ai-buyer`
- **Action**:
  1. **Tab 1 (12-Stage API Buyer)**: Click **"Run 12-Stage Simulation"** to watch the machine-to-machine REST/MCP execution from tool discovery down to order creation.
  2. **Tab 2 (Agent-to-Agent Commerce)**: Click **"Simulate A2A Commerce"** to watch an external Customer AI Agent negotiate and transact with the Merchant Shopping Agent via REST endpoints.

---

### 5. Growth, Dynamic Pricing & What-If Simulation (3:15 - 4:00)
- **Navigate to**: `/pricing`
  - Select *ProRunner X1* → adjust demand velocity slider (1.5x) and competitor shift (+5%) → view suggested dynamic price, elasticity score, and estimated revenue impact.
- **Navigate to**: `/simulator`
  - Adjust promotional discount (10%) and inventory scaling (+20%) → review projected revenue lift, order volume delta, and profit margins.
- **Navigate to**: `/growth`
  - Review AI Recommendation telemetry, A/B Testing pricing variants, and ask the **Merchant AI Copilot** strategic store questions.

---

### 6. Tamper-Evident Audit Verification (4:00 - 4:30)
- **Navigate to**: `/audit`
- **Action**:
  1. Review the cryptographic SHA-256 hash-chained event logs showing `event_hash` and `previous_hash`.
  2. Click **"Verify Hash Chain Integrity"**.
  3. The system validates all hashes from Genesis (`000...`) and confirms **"Audit Chain Valid: N Events Cryptographically Verified"**.

---

### 7. Decision Replay, Live Telemetry & Security Lab (4:30 - 5:00)
- **Navigate to**: `/decisions`
  - Select any completed transaction → view the interactive **15-Stage Decision Replay** reconstructing the exact journey from prompt to webhook.
- **Navigate to**: `/notifications`
  - Show real-time security alerts and human approval queue.
- **Navigate to**: `/live`
  - View real-time agent event telemetry, latency metrics (Agent: 245ms, Tool: 42ms, Payment: 310ms), and AI commercial ROI.
- **Navigate to**: `/security`
  - Click **"Execute All 15 Scenarios"** → show real-time protection against purchase limit breaches, excessive discounts, prompt injection, velocity violations, circuit breaker trips, and client price tampering.

---

### 🏁 Closing Statement
> *"AgentPay AI transforms AI commerce from an unmonitored security risk into a governed, transparent, revenue-generating reality for modern merchants and Razorpay."*
