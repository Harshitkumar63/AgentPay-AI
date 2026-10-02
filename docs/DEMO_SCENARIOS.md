# AgentPay AI — Interactive Demo Scenarios & Script

This document details 8 end-to-end scenarios to demonstrate the full power of AgentPay AI during presentations and evaluations.

---

## Scenario 1: Autonomous Governed Discovery & Checkout
1. Open the frontend dashboard: `http://localhost:3000/shop`
2. Chat with the Shopping Assistant:
   > *"I want comfortable shoes for marathon training under ₹3,000."*
3. The agent searches catalog, inspects inventory, explains decision factors, adds product to cart, and calculates server pricing.
4. If amount $\le$ limit, order is automatically created in `APPROVED` status.

---

## Scenario 2: High-Value Human-in-the-Loop Authorization
1. Chat with the agent:
   > *"Buy 3 pairs of Pro Runner Shoes for ₹7,500 total."*
2. Risk score engine scores the order at 95 (CRITICAL) due to high transaction value.
3. Order is placed in `APPROVAL_PENDING` with a 5-minute countdown TTL.
4. Navigate to `/orders` or `/notifications` -> Click **Approve Transaction**.
5. Order immediately advances to `APPROVED` and opens Razorpay Test Mode checkout.

---

## Scenario 3: Controlled Machine-to-Machine Negotiation
1. Navigate to `/ai-buyer` or use `POST /api/a2a/simulate`.
2. Buyer agent proposes a 15% discount on headphones.
3. Merchant policy caps discount at 12%.
4. Backend negotiation engine mathematically calculates the maximum permissible offer and responds deterministically.
5. Buyer agent reviews and confirms order.

---

## Scenario 4: Global Emergency Kill Switch
1. Navigate to `/agents` -> Click **Emergency Pause All Operations**.
2. Try placing an order via Python SDK or chat.
3. System immediately blocks order creation with `SYSTEM_PAUSED`.
4. Catalog search and revenue analytics remain active and readable.
5. Click **Resume All** to return to nominal status.

---

## Scenario 5: Circuit Breaker Auto-Trip & Cooldown
1. Navigate to `/security` -> Trigger 5 simulated payment declines for `ShoppingBot`.
2. The Circuit Breaker trips to `OPEN` and logs `CIRCUIT_OPENED` in audit trail.
3. Any subsequent checkout attempts are blocked with `CIRCUIT_OPEN`.
4. After 60 seconds (or manual admin reset), circuit transitions to `HALF_OPEN` to test a single probe transaction.

---

## Scenario 6: Cryptographic Tamper-Evident Audit Verification
1. Navigate to `/audit`.
2. Review the live SHA-256 hash-chained event stream with event hashes and previous hashes.
3. Click **Verify Hash Chain Integrity**.
4. The system validates all hashes from Genesis (`000...`) and confirms `100% Valid & Un-tampered`.

---

## Scenario 7: Idempotency Conflict Protection
1. Send an order creation request with `Idempotency-Key: idem_demo_100` and cart #1.
2. Re-send the exact same request -> Backend returns the existing order safely.
3. Send a different cart with `Idempotency-Key: idem_demo_100` -> Backend immediately rejects with `409 IDEMPOTENCY_CONFLICT`.

---

## Scenario 8: Multi-Agent Model Context Protocol (MCP) Execution
1. Send an MCP tool execution to `POST /api/mcp/call` with `tool_name: search_products`.
2. Backend authenticates caller, validates scoped permissions in Agent Registry, executes deterministic search, and logs a tamper-evident audit record.
