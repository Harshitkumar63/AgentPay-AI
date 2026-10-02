# Decision Replay V2 — 15-Stage Structured Audit Specification

## Overview
Decision Replay provides a transparent, auditable step-by-step trace of every thought, permission check, policy evaluation, and financial execution performed during an agentic commerce session.

---

## 15-Stage Decision Pipeline

1. **`USER_INTENT`**: Natural language objective and constraints received from the customer.
2. **`CONTEXT_RETRIEVAL`**: Session memory and customer preferences retrieved from database.
3. **`TOOL_SELECTION`**: LLM selects next tool call based on objective.
4. **`AGENT_AUTHENTICATION`**: API key verified against stored SHA-256 hash.
5. **`PERMISSION_CHECK`**: Explicit tool permission verified in Agent Registry.
6. **`KILL_SWITCH_CHECK`**: Global system controls and module flags verified enabled.
7. **`CIRCUIT_BREAKER_CHECK`**: Failure counters evaluated to ensure circuit is `CLOSED` or `HALF_OPEN`.
8. **`VELOCITY_LIMIT_CHECK`**: Sliding window timestamp checked against per-minute/hourly frequency caps.
9. **`CATALOG_PRICE_VALIDATION`**: Product price and live stock re-verified from database.
10. **`POLICY_EVALUATION`**: Merchant limits (purchase cap, discount ceiling) evaluated.
11. **`RISK_SCORING`**: Continuous 0-100 deterministic risk engine scores transaction.
12. **`DYNAMIC_BUDGET_CHECK`**: Daily budget balance and trust spending tier limit validated.
13. **`APPROVAL_GATING`**: 5-minute human approval record created if risk $\ge$ threshold.
14. **`ORDER_TRANSITION`**: Deterministic 12-state machine advances state.
15. **`AUDIT_HASH_CHAIN`**: Decision metadata and event payload cryptographically chained to predecessor.

---

## Decision Replay API
- **Endpoint**: `GET /api/agent/v1/decisions/replay/{order_id}`
- **Response**: Full structured array of all 15 stages with timestamps, inputs, outputs, decisions, and mathematical SHA-256 event hashes.
