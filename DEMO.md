# AgentPay AI — Live Demonstration Script (3-5 Minutes)

This script provides a structured, high-impact demonstration of the **AgentPay AI** platform.

---

## ⏱️ Timeline Overview

| Timestamp | Section | Key Feature Demonstrated |
|-----------|---------|--------------------------|
| **0:00 - 0:45** | **1. The Problem & Vision** | Autonomous Agentic Commerce & Governance Challenge |
| **0:45 - 1:45** | **2. AI Conversational Shop** | Catalog Search, Recommendation Scoring, Human Approval Gate |
| **1:45 - 2:30** | **3. AI Buyer Simulator** | 12-Step Machine-to-Machine Autonomous Commerce via REST/MCP |
| **2:30 - 3:15** | **4. Governance & Security Lab** | 10 Controlled Security Tests & Policy Simulator |
| **3:15 - 4:15** | **5. Growth Center & Copilot** | Upsell/Cross-sell Analytics & Merchant AI Copilot |
| **4:15 - 5:00** | **6. Decision Replay & Audit** | 100% Data-Backed Autonomous Journey Reconstruction |

---

## 🎬 Step-by-Step Presentation Guide

### 1. The Problem & Vision (0:00 - 0:45)
- **Goal**: Introduce how AI shopping agents are changing e-commerce, and why merchants need deterministic safety.
- **Talking Point**:
  > *"As autonomous AI agents begin shopping on behalf of users, merchants need more than just a chatbot — they need a secure, policy-gated infrastructure that prevents rogue spending, protects margins, ensures human authorization, and integrates directly with Razorpay."*

---

### 2. AI Conversational Shop & Human Approval Gate (0:45 - 1:45)
- **Navigate to**: `/shop`
- **Action**:
  1. Click quick prompt: `Find black running shoes under ₹3000`.
  2. Notice the instant catalog extraction, inventory badge, and **Score: 95/100** recommendation badge.
  3. Click **"Add to Cart"** on *ProRunner X1 Running Shoes*.
  4. Click **"Gated AI Checkout"** in the live cart sidebar.
  5. The **Human Approval & Governance Review Modal** appears:
     - Policy Check: `ALLOWED`
     - Risk Assessment: `HIGH RISK (FINANCIAL)`
     - Agent Budget: `AVAILABLE`
     - Agent Trust Score: `87/100`
     - Approval: `REQUIRED (5-minute TTL)`
  6. Click **"Confirm Purchase"** to trigger Razorpay Test Mode verification and complete checkout.

---

### 3. AI Buyer Simulator (1:45 - 2:30)
- **Navigate to**: `/ai-buyer`
- **Action**:
  1. Show the goal: `Buy a SwiftBook laptop under ₹50000`.
  2. Click **"Run Autonomous Agent Simulation"**.
  3. Watch the live 12-step machine-to-machine pipeline execute in real time:
     - Discover MCP Tools → Search Catalog → Compare Products → Check Live Stock → Initialize Cart → Recalculate Pricing Server-Side → Policy Engine → Risk Engine → Budget & Trust → Human Gate → Order Creation.
  4. Inspect the live JSON responses in the inspector.

---

### 4. Security & Failure Demonstration Lab (2:30 - 3:15)
- **Navigate to**: `/security`
- **Action**:
  1. Point out the **10 controlled scenarios** protecting the platform against rogue agents, margin drain, and gateway dropouts.
  2. Click **"Execute All 10 Scenarios"** or run **"Purchase Limit Breach"** and **"Duplicate Webhook Replay Attack"**.
  3. Show the real-time breakdown of `INPUT` → `VALIDATION` → `POLICY` → `RISK` → `AUDIT`.
- **Navigate to**: `/policies/simulator`
- **Action**:
  1. Enter ₹7,500 and 10% discount.
  2. Click **"Run Policy Simulation"** to display real-time deterministic policy evaluation.

---

### 5. Merchant Growth Center & AI Copilot (3:15 - 4:15)
- **Navigate to**: `/growth`
- **Action**:
  1. Point out the clear distinction between **Actual Captured Revenue** and **Estimated Growth Opportunity**.
  2. Showcase the **AI Recommendation & Conversion Telemetry** (Impressions, Clicks, Purchases, CTR, and Conversion Rates).
  3. Ask the **Merchant AI Copilot**: *"Why did revenue change this month?"*
  4. Review the dynamic answer, suggested actions, and the **AI Campaign Proposal**.
  5. Click **"Approve & Activate"** on the campaign proposal.

---

### 6. Order Timeline & Decision Replay (4:15 - 5:00)
- **Navigate to**: `/orders`
- **Action**:
  1. Click on the most recent completed order.
  2. View the step-by-step state machine timeline with real timestamps and actors.
  3. Click **"View Decision Replay"**.
  4. Walk through the reconstructed autonomous journey from user prompt down to Razorpay signature verification and audit trail.
- **Closing Statement**:
  > *"AgentPay AI turns AI commerce from a speculative risk into a governed, revenue-generating reality for modern merchants."*
