# AgentPay AI — Complete REST & MCP API Reference

## Base URLs
- Local Development: `http://localhost:8000`
- API Prefix: `/api`
- Machine-Readable Manifest: `/.well-known/agent.json`

---

## Authentication
Pass agent API key in headers:
```http
X-Agent-Key: agp_3e8f8101a24d4b1a89c099e2e28a49c2
Authorization: Bearer agp_3e8f8101a24d4b1a89c099e2e28a49c2
```

---

## 1. Admin Agent Registry Endpoints

### `POST /api/admin/agents`
Registers a new autonomous AI agent and returns an issued API key.
**Request**:
```json
{
  "name": "Procurement Agent 01",
  "description": "Searches catalog and negotiates bulk items",
  "role": "shopping",
  "owner": "admin",
  "permissions": ["catalog.read", "product.search", "cart.write", "checkout.request"],
  "daily_budget": 10000.0,
  "transaction_limit": 5000.0
}
```
**Response**:
```json
{
  "success": true,
  "agent": {
    "id": "agent_a7f920bc",
    "name": "Procurement Agent 01",
    "status": "ACTIVE",
    "api_key_prefix": "agp_3e8f..."
  },
  "api_key": "agp_3e8f8101a24d4b1a89c099e2e28a49c2",
  "message": "Agent registered successfully. Store API key safely."
}
```

### `GET /api/admin/agents`
List all registered agents, their trust scores, budgets, and circuit breaker states.

### `GET /api/admin/agents/{id}`
Retrieve full agent profile, permissions, and operational statistics.

### `POST /api/admin/agents/{id}/rotate-key`
Generate a new API key and invalidate prior key hash.

### `POST /api/admin/agents/{id}/pause`
Emergency halt of agent operations.

### `POST /api/admin/agents/{id}/resume`
Resume normal agent execution.

---

## 2. Admin System Controls & Global Kill Switch

### `GET /api/admin/system/status`
Returns global system operational flags:
```json
{
  "global_write_enabled": true,
  "payments_enabled": true,
  "campaigns_enabled": true,
  "agent_execution_enabled": true,
  "status": "NORMAL",
  "last_reason": "System initialized in normal operational state"
}
```

### `POST /api/admin/system/pause`
Emergency global freeze of all writes, payments, and agent actions.

### `POST /api/admin/system/resume`
Resume all normal operations across modules.

### `POST /api/admin/system/pause-payments`
Pauses financial checkout and payment creation while keeping catalog discovery active.

### `POST /api/admin/system/pause-agents`
Pauses autonomous AI agents while human merchant operations remain active.

---

## 3. Human Approval System

### `GET /api/admin/approvals`
List pending and resolved approval authorizations (`?status=PENDING`).

### `POST /api/admin/approvals/{id}/approve`
Approve a high-risk or gated transaction within the 5-minute TTL window.

### `POST /api/admin/approvals/{id}/reject`
Reject a gated transaction.

---

## 4. Tamper-Evident Audit Trail

### `GET /api/admin/audit/verify`
Cryptographically verifies the mathematical integrity of the SHA-256 hash chain:
```json
{
  "valid": true,
  "events_checked": 120,
  "latest_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

### `GET /api/admin/audit`
Paginated audit log records with chained parent hashes and execution metadata.

---

## 5. Agent-to-Agent (A2A) Commerce

- `POST /api/a2a/discovery`: Search products and negotiate parameters.
- `POST /api/a2a/request`: Request binding quote and max promotional band.
- `POST /api/a2a/offer`: Submit autonomous price proposal.
- `POST /api/a2a/accept`: Accept offer and initiate gated checkout.
- `POST /api/a2a/reject`: Record negotiation termination telemetry.
- `POST /api/a2a/simulate`: Full 6-stage end-to-end simulation.

---

## 6. Model Context Protocol (MCP)

### `GET /api/mcp/tools`
Returns JSON Schema definitions for all 16 MCP tools:
1. `search_products`
2. `get_product`
3. `compare_products`
4. `create_cart`
5. `add_to_cart`
6. `get_cart`
7. `get_recommendations`
8. `evaluate_policy`
9. `evaluate_risk`
10. `get_agent_budget`
11. `get_agent_trust`
12. `request_approval`
13. `create_order`
14. `get_order_status`
15. `get_payment_status`
16. `get_audit_trace`

### `POST /api/mcp/call`
Execute any tool with automated authentication, permission check, and audit log generation:
```json
{
  "tool_name": "search_products",
  "arguments": {
    "query": "running shoes",
    "max_price": 3500.0
  }
}
```
