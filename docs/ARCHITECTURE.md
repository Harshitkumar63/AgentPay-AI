# AgentPay AI — System Architecture & Technical Specifications

AgentPay AI is a production-grade Agentic Commerce platform designed to enable autonomous AI shopping agents, machine-to-machine commerce, algorithmic revenue optimization, and deterministic governance on top of Razorpay Test Mode.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph "External & Internal AI Agents"
        UserChat["Customer UI / Conversational Chat"]
        ExternalAgent["Autonomous External AI Buyer (REST/MCP)"]
        MerchantCopilot["Merchant AI Copilot"]
    end

    subgraph "AgentPay AI Gateway & API Layer"
        ToolsRegistry["Tools Registry & Spec (/agent/v1/tools)"]
        AgentRouter["Agent Orchestrator (18 Tools & 16 Trace Stages)"]
        CatalogAPI["AI Catalog & Search Engine"]
        CartAPI["Server-Side Cart & Pricing Engine"]
        OrderAPI["State Machine Order Service"]
        PaymentAPI["Razorpay Payment Service"]
        WebhookAPI["Webhook Replay & Idempotency Monitor"]
    end

    subgraph "Deterministic Governance Core"
        PolicyEngine["Deterministic Policy Engine"]
        RiskEngine["Deterministic Risk Engine (LOW/MED/HIGH)"]
        BudgetEngine["Agent Budget & Spending Guard"]
        TrustEngine["Server-Side Agent Trust Score (0-100)"]
        ApprovalGate["Human-in-the-Loop Approval Gate (5m TTL)"]
        AuditEngine["Persistent Audit Logger"]
    end

    subgraph "Database & Financial Gateway"
        DB[(Relational DB / SQLite / Postgres)]
        RazorpayGateway["Razorpay Payment Gateway (Test Mode)"]
    end

    UserChat --> AgentRouter
    ExternalAgent --> ToolsRegistry
    ExternalAgent --> CartAPI
    MerchantCopilot --> AgentRouter

    AgentRouter --> PolicyEngine
    CartAPI --> PolicyEngine
    PolicyEngine --> RiskEngine
    PolicyEngine --> BudgetEngine
    PolicyEngine --> TrustEngine
    BudgetEngine --> ApprovalGate
    ApprovalGate --> OrderAPI
    OrderAPI --> PaymentAPI
    PaymentAPI --> RazorpayGateway
    RazorpayGateway --> WebhookAPI
    WebhookAPI --> AuditEngine
    AuditEngine --> DB
```

---

## 2. 16-Stage Autonomous Commerce Pipeline

Every commercial operation undergoes a deterministic, verifiable 16-stage pipeline:

```mermaid
sequenceDiagram
    autonumber
    actor Customer as User / AI Agent
    participant Agent as Shopping Agent
    participant Catalog as Product Catalog
    participant Recs as Recommendation Engine
    participant Cart as Cart Service
    participant Policy as Policy & Risk Engine
    participant Budget as Budget & Trust Service
    participant Approval as Human Approval Gate
    participant OrderSvc as Order State Machine
    participant PaySvc as Payment Service
    participant Gateway as Razorpay (Test Mode)
    participant Webhook as Webhook Monitor
    participant Audit as Audit Logger

    Customer->>Agent: "Buy running shoes & accessories under ₹3000"
    Agent->>Catalog: search_products(query, max_price)
    Catalog-->>Agent: Product Matches
    Agent->>Recs: get_recommendations(prod_001, cross_sell)
    Recs-->>Agent: Ranked Accessory Recommendations
    Agent->>Cart: add_item(prod_001), add_item(prod_002)
    Cart->>Cart: Recalculate Subtotal, Discounts & Tax Server-Side
    Cart->>Policy: check_purchase_policy(amount, discount, action)
    Policy->>Policy: Evaluate Merchant Limits & Discount Caps
    Policy->>Budget: check_agent_budget(daily, per_transaction)
    Budget-->>Policy: Budget Available & Trust Tier Verified
    Policy-->>Agent: ALLOWED (Risk: HIGH, Approval: REQUIRED)
    Agent->>Approval: create_approval_request(5m TTL)
    Approval-->>Customer: Render Human Review Modal
    Customer->>Approval: Grant Approval Decision
    Approval->>OrderSvc: create_order(cart_id, idempotency_key)
    OrderSvc->>PaySvc: create_payment_for_order(order_id)
    PaySvc->>Gateway: Create Razorpay Order
    Gateway-->>PaySvc: razorpay_order_id
    PaySvc-->>Customer: Razorpay Checkout Handler
    Customer->>Gateway: Submit Test Payment
    Gateway->>Webhook: webhook(payment.captured, HMAC SHA256)
    Webhook->>Webhook: Idempotency Signature Verification
    Webhook->>OrderSvc: Transition status -> COMPLETED
    OrderSvc->>Audit: Commit Immutable Transaction Record
```

---

## 3. Security & Governance Principles

1. **Deterministic Execution**:
   - Risk scoring and policy evaluations are calculated using pure deterministic algorithms.
   - LLMs have zero ability to execute arbitrary payment API calls or access secret credentials.
2. **Server-Side Price Authority**:
   - Client-submitted totals or unit prices are discarded; all charges are recalculated from active database pricing.
3. **Idempotency & Replay Resistance**:
   - Unique idempotency keys on checkout prevent double charges.
   - Webhook events are hashed and recorded; duplicate webhook delivery is safely ignored.
4. **Time-Limited Human Authorization**:
   - Human approvals strictly expire after a 5-minute TTL. Stale approval tokens are rejected automatically.
5. **Agent Budget & Trust Guardrails**:
   - Agents are bound by daily spending limits and single transaction caps.
   - Trust scores (0–100) adjust dynamically based on transaction success rates, payment failures, and policy violations.

---

## 4. State Machine Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Cart Initialized
    DRAFT --> POLICY_CHECK: Items Added
    POLICY_CHECK --> BLOCKED: Policy Limit / Cap Exceeded
    POLICY_CHECK --> APPROVAL_PENDING: Risk High / Approval Mandated
    APPROVAL_PENDING --> CANCELLED: Human Rejected
    APPROVAL_PENDING --> EXPIRED: TTL Elapsed (> 5m)
    APPROVAL_PENDING --> ORDER_CREATED: Human Approved
    POLICY_CHECK --> ORDER_CREATED: Low Risk (Auto-Approved)
    ORDER_CREATED --> PAYMENT_PENDING: Razorpay Order Initialized
    PAYMENT_PENDING --> PAYMENT_FAILED: Bank Decline / Network Timeout
    PAYMENT_FAILED --> PAYMENT_PENDING: Safe Retry
    PAYMENT_PENDING --> PAYMENT_CAPTURED: Webhook Verified
    PAYMENT_CAPTURED --> COMPLETED: Fulfillment Committed
    COMPLETED --> [*]
```
