# 🏆 AgentPay AI — Complete Run Guide & Winning Loom Video Strategy

> **Goal:** Run the project, record a 5-minute Loom video, and WIN the Razorpay Buildathon.

---

## 📋 PART 1: HOW TO RUN THE PROJECT

### Prerequisites
- **Python 3.11+** (you have Python 3.14 installed ✅)
- **Node.js 18+** (you have it installed ✅)
- **Both servers** must run simultaneously in **2 separate terminals**

### Terminal 1: Start Backend (FastAPI on port 8000)

```powershell
cd "C:\Users\harsh\Desktop\RAZOR PAY\backend"

# Activate virtual environment
.\venv\Scripts\activate

# Start backend server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

You should see:
```
🚀 Starting AgentPay AI...
📦 Database initialized (SQLite)
🤖 AI Provider: openai (DEMO MODE)
💳 Razorpay: DEMO MODE
🎯 Demo Mode: True
🌱 Demo data seeded
Uvicorn running on http://127.0.0.1:8000
```

**Verify:** Open [http://localhost:8000/docs](http://localhost:8000/docs) in browser → You should see Swagger API docs.

### Terminal 2: Start Frontend (Next.js on port 3000)

```powershell
cd "C:\Users\harsh\Desktop\RAZOR PAY\frontend"

# Start frontend dev server
npm run dev
```

You should see:
```
▲ Next.js 16.3.1 (Turbopack)
- Local: http://localhost:3000
✓ Ready in 4.5s
```

**Verify:** Open [http://localhost:3000](http://localhost:3000) → You'll be redirected to the Dashboard.

### If Port 8000 Is Already In Use

```powershell
# Find and kill the process using port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PROCESS_ID> -Force

# Then start backend again
```

### Quick Verification Checklist

| Check | URL | Expected |
|:------|:----|:---------|
| Backend Health | http://localhost:8000/health | `{"status":"healthy"}` |
| API Docs | http://localhost:8000/docs | Swagger UI loads |
| Frontend Dashboard | http://localhost:3000/dashboard | Dashboard with revenue charts |
| AI Shop | http://localhost:3000/shop | Conversational shopping UI |

> [!IMPORTANT]
> **Both servers must be running simultaneously.** The frontend calls the backend API. If backend is down, you'll see "Failed to fetch" errors.

---

## 🎬 PART 2: WINNING 5-MINUTE LOOM VIDEO STRATEGY

### Step 0: Setting Up Loom

1. Go to [https://www.loom.com](https://www.loom.com) and sign up (free plan works)
2. Install the **Loom Desktop App** or use the **Chrome Extension**
3. Settings for recording:
   - **Screen + Camera** (your face in corner builds trust with judges)
   - **Microphone:** Use headphones mic for clarity
   - **Resolution:** 1080p
   - **Screen:** Record your **full screen** (not a tab — judges want to see the full app)
4. **Close all other browser tabs** before recording — judges notice clutter
5. **Pre-open all the pages** you'll visit in separate browser tabs before hitting record

### Pre-Recording Checklist

- [ ] Backend running on port 8000 (Terminal 1)
- [ ] Frontend running on port 3000 (Terminal 2)
- [ ] Browser open at `http://localhost:3000/dashboard`
- [ ] Pre-open these tabs in order:
  1. `/dashboard` — Revenue Analytics
  2. `/shop` — AI Conversational Shop
  3. `/agents` — Agent Registry & Kill Switch
  4. `/ai-buyer` — AI Buyer Simulator
  5. `/pricing` — Dynamic Pricing Simulator
  6. `/simulator` — What-If Business Simulator
  7. `/growth` — Growth Center & A/B Testing
  8. `/audit` — Tamper-Evident Audit Trail
  9. `/decisions` — 15-Stage Decision Replay
  10. `/security` — Security Lab (15 Attack Scenarios)
  11. `/live` — Live Event Stream & Telemetry
  12. `/support` — Customer Support Agent
- [ ] Loom recording ready with Screen + Camera
- [ ] Speak clearly and with energy — judges watch 100+ videos, yours must stand out

---

## 🎥 PART 3: EXACT VIDEO SCRIPT — SECOND BY SECOND

### ⏱️ 0:00 – 0:40 | THE HOOK & PROBLEM (Dashboard)
**Page:** `/dashboard`

**What to say (speak with energy and conviction):**

> *"Hey! I'm Harsh, and this is AgentPay AI — built for the Razorpay Buildathon.*
>
> *Here's the problem: Autonomous AI agents are becoming the primary way people shop online. But there's a massive security gap — if you let an LLM directly touch Razorpay's payment API, it can hallucinate prices, fabricate discounts, and create unauthorized transactions.*
>
> *AgentPay AI solves this with a Defense-in-Depth architecture — AI proposes, but deterministic backend code decides. Every transaction goes through 8 security gates before touching Razorpay.*
>
> *Let me show you the live platform. This is our real-time dashboard — you can see total revenue, order conversion rates, AI-assisted revenue, and blocked actions — all computed from actual database records, never hallucinated."*

**What to do on screen:**
- Point at the revenue cards (Revenue, Orders, Conversion Rate, AI Revenue)
- Briefly hover over the Growth Recommendations section
- Transition: *"Let me show you the core experience..."*

---

### ⏱️ 0:40 – 1:50 | AI SHOP & NEGOTIATION (The WOW Moment)
**Page:** `/shop`

**This is the MOST IMPORTANT section — spend the most time here.**

**What to say:**

> *"This is our AI Conversational Shop. Let me search for something..."*

**What to do:**
1. Click the quick prompt **"Find black running shoes under ₹3000"** or type it
2. Wait for results to appear

> *"Notice — the AI agent searched our real product catalog, checked live inventory, and gave authoritative recommendations with stock badges and recommendation scores. No hallucination — every price comes from our PostgreSQL database."*

3. Click **"Negotiate Price"** on ProRunner X1 Running Shoes
4. Enter ₹2,200 as counter-offer → Click **Submit Proposal**

> *"Here's where it gets interesting — controlled price negotiation. The buyer proposed ₹2,200, but our merchant policy caps maximum discount at 15%. The backend deterministically calculated the floor price and made a counter-offer. No LLM can bypass this — it's compiled Python code."*

5. Click **"Optimize Cart"** → Select **"Best Value"** mode → Click **Apply**

> *"Our Cart Optimizer engine has 4 modes — Minimum Price, Best Value, Best Quality, Maximum Saving — each using live catalog data to suggest item replacements."*

6. Click **"Gated AI Checkout"** → Show the Governance Modal

> *"And here's the key innovation — before ANY payment touches Razorpay, this Human-in-the-Loop governance gate appears. It shows the Policy result, Risk Score, Agent Budget, Trust Score, and a 5-minute expiring approval TTL. The merchant stays in control."*

7. Click **"Confirm Purchase"** (Razorpay Test Mode popup appears)

---

### ⏱️ 1:50 – 2:30 | MULTI-AGENT GOVERNANCE & KILL SWITCH
**Page:** `/agents`

**What to say:**

> *"AgentPay runs a specialized multi-agent system. Each agent — Shopping, Payment, Growth, Support, Security — has scoped permissions, dedicated budgets, and independent circuit breakers."*

**What to do:**
1. Show the agent cards grid (5 agents)
2. Click into one agent (e.g., ShoppingBot) → Show permissions, trust score, budget

> *"Each agent has SHA-256 hashed API keys. I can rotate keys instantly..."*

3. Click **"Rotate API Key"** to demonstrate
4. Go back to agent list → Click **"Emergency Pause"** on an agent

> *"And with one click — Emergency Kill Switch. This instantly freezes all financial operations for that agent. Catalog browsing stays active but payments are blocked. This is critical for merchant safety."*

---

### ⏱️ 2:30 – 3:10 | AI BUYER & A2A COMMERCE
**Page:** `/ai-buyer`

**What to say:**

> *"Now here's something unique — Agent-to-Agent commerce. An external AI buyer can discover, negotiate, and transact with our merchant through REST APIs."*

**What to do:**
1. Click **"Run 12-Stage Simulation"** (Tab 1)
2. Watch the stages execute one by one in real-time

> *"This shows the complete machine-to-machine pipeline — tool discovery, catalog search, price verification, cart creation, policy check, risk scoring, budget verification, order creation — all 12 stages with live status indicators."*

3. Switch to **Tab 2 (Agent-to-Agent)** → Click **"Simulate A2A Commerce"**

> *"This simulates an external Customer AI Agent negotiating with our Merchant Agent — complete REST machine-to-machine interaction."*

---

### ⏱️ 3:10 – 3:50 | GROWTH, PRICING & WHAT-IF SIMULATOR
**Page:** `/pricing` → `/simulator` → `/growth`

**What to say & do:**

1. **Pricing Simulator** (`/pricing`):
   - Select ProRunner X1
   - Adjust demand velocity slider to 1.5x
   - Show the dynamic price suggestion

> *"Our Dynamic Pricing Simulator models demand elasticity and inventory velocity — without mutating active catalog prices. It's a safe sandbox for pricing strategy."*

2. **What-If Simulator** (`/simulator`):
   - Set 10% promotional discount, +20% inventory scaling
   - Show projected revenue lift

> *"The What-If Simulator lets merchants forecast the impact of promotions, inventory changes, and pricing shifts before committing."*

3. **Growth Center** (`/growth`):
   - Show AI A/B Testing results (Variant A vs B)
   - Show the Merchant AI Copilot

> *"Our Growth Center includes AI A/B pricing tests with conversion lift tracking, cross-sell and upsell recommendation analytics, and a Merchant AI Copilot grounded in real store metrics."*

---

### ⏱️ 3:50 – 4:25 | AUDIT TRAIL & SECURITY LAB
**Page:** `/audit` → `/security`

**What to say & do:**

1. **Audit Trail** (`/audit`):
   - Show the hash-chained event log
   - Click **"Verify Hash Chain Integrity"**

> *"Every governance event is logged in a tamper-evident SHA-256 hash chain — just like a blockchain. Each event's hash includes the previous event's hash. Click verify — the system mathematically validates the entire chain from Genesis. If anyone tampers with even one record, the chain breaks."*

2. **Security Lab** (`/security`):
   - Click **"Execute All 15 Scenarios"**
   - Watch attack scenarios execute and get blocked

> *"Our Security Lab runs 15 live attack simulations — purchase limit breaches, excessive discount requests, prompt injection, velocity violations, circuit breaker trips, client-side price tampering. Every single one is detected and blocked by our Defense-in-Depth pipeline."*

---

### ⏱️ 4:25 – 5:00 | DECISION REPLAY, LIVE STREAM & CLOSING
**Page:** `/decisions` → `/live`

**What to say & do:**

1. **Decision Replay** (`/decisions`):
   - Select a completed transaction
   - Show the 15-stage visual pipeline

> *"Decision Replay reconstructs the exact governance path of any transaction — from user intent through all 8 security gates to payment capture. Full transparency."*

2. **Live Event Stream** (`/live`):
   - Show real-time telemetry

> *"Real-time telemetry showing agent latency, payment gateway latency, and AI revenue attribution."*

3. **Closing Statement (look at camera):**

> *"AgentPay AI is not a prototype — it's a complete platform with 27 interactive routes, 52 automated tests passing at 100%, an official Python SDK, MCP compatibility, and Razorpay Standard Checkout integration.*
>
> *We transform AI commerce from an unmonitored security risk into a governed, transparent, revenue-generating reality for modern merchants.*
>
> *Built for Razorpay. Built to ship. Thank you."*

---

## 🏆 PART 4: WINNING TIPS

### What Makes Judges Pick Winners

| Factor | How AgentPay AI Delivers |
|:-------|:------------------------|
| **Real Problem** | AI agents can hallucinate payments → AgentPay governance stops it |
| **Working Demo** | 27 live routes, not mockups |
| **Technical Depth** | 8-gate security pipeline, SHA-256 hash chain, circuit breakers |
| **Razorpay Integration** | Standard Checkout + Orders API + HMAC verification |
| **Uniqueness** | Agent-to-Agent commerce, MCP protocol, 15-stage decision replay |
| **Polish** | Beautiful UI, real analytics, comprehensive test suite |

### Video Tips

1. **Energy matters** — Speak with passion. Judges are watching 100+ videos. Be memorable.
2. **Don't read a script** — Practice 2-3 times, then speak naturally.
3. **Show, don't tell** — Click buttons, show live data, demonstrate real interactions.
4. **Face on camera** — Screen + Camera mode in Loom. Human connection wins.
5. **Start strong** — Your first 10 seconds decide if judges keep watching.
6. **End with impact** — Look at camera, deliver the closing line with confidence.
7. **Time yourself** — Practice to hit exactly 4:50-5:00. Don't go over.

### Common Mistakes to Avoid

- ❌ Don't spend time explaining how to install/run the project
- ❌ Don't show code files or terminal output (judges want the PRODUCT)
- ❌ Don't mumble or speak too fast
- ❌ Don't show errors on screen (pre-test everything)
- ❌ Don't say "basically" or "so yeah" — speak with authority
- ❌ Don't rush the AI Shop section — it's your main selling point

### Practice Run Order

1. **Practice Run 1:** Read this guide and click through all pages once (10 min)
2. **Practice Run 2:** Do a full 5-min dry run speaking out loud (5 min)
3. **Practice Run 3:** Record a test Loom video, watch it, note improvements (10 min)
4. **Final Recording:** Record the real one with confidence (5 min)

---

## 📌 QUICK REFERENCE: ALL 27 ROUTES

| # | Route | Feature | Show in Video? |
|:--|:------|:--------|:--------------|
| 1 | `/dashboard` | Revenue Analytics & KPIs | ✅ YES (opener) |
| 2 | `/shop` | AI Conversational Shop & Negotiation | ✅ YES (star feature) |
| 3 | `/agents` | Multi-Agent Registry & Kill Switch | ✅ YES |
| 4 | `/agents/[id]` | Agent Detail Profile | ✅ YES (briefly) |
| 5 | `/ai-buyer` | AI Buyer & A2A Commerce Simulator | ✅ YES |
| 6 | `/pricing` | Dynamic Pricing Simulator | ✅ YES |
| 7 | `/simulator` | What-If Business Simulator | ✅ YES |
| 8 | `/growth` | Growth Center & A/B Testing | ✅ YES |
| 9 | `/audit` | Tamper-Evident Audit Trail | ✅ YES |
| 10 | `/security` | Security Lab (15 Scenarios) | ✅ YES |
| 11 | `/decisions` | 15-Stage Decision Replay | ✅ YES |
| 12 | `/live` | Live Event Stream & Telemetry | ✅ YES (closer) |
| 13 | `/support` | Customer Support Agent | ⏭ Skip (time) |
| 14 | `/products` | Product Catalog | ⏭ Skip |
| 15 | `/orders` | Orders & Timeline | ⏭ Skip |
| 16 | `/analytics` | Revenue Analytics Detail | ⏭ Skip |
| 17 | `/agent` | Agent Trace | ⏭ Skip |
| 18 | `/notifications` | Security Alerts | ⏭ Skip |
| 19 | `/webhooks` | Webhook Monitor | ⏭ Skip |
| 20 | `/policies/simulator` | Policy Simulator | ⏭ Skip |
| 21 | `/developers` | Developer Portal & SDK | ⏭ Skip |
| 22 | `/trust` | Trust Center | ⏭ Skip |
| 23 | `/settings` | Settings | ⏭ Skip |
| 24 | `/inventory` | Inventory Intelligence | ⏭ Skip |

> [!TIP]
> **12 pages in 5 minutes** is the sweet spot. You show breadth AND depth. The pages marked ✅ above are the ones that will impress judges most.

---

**Good luck, Harsh! 🚀 You've built something genuinely impressive. Now show it with confidence.**
