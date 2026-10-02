# Developer Guide — Building Autonomous AI Agents with AgentPay AI

## Overview
AgentPay AI provides three clean ways for autonomous AI agents, multi-agent frameworks (LangChain, AutoGen, CrewAI), and LLMs to interact with commerce:

1. **Official Python SDK** (`sdk/agentpay/`)
2. **Model Context Protocol (MCP)** (`/api/mcp/tools` & `/api/mcp/call`)
3. **Direct Governed HTTP REST API** (`/api/agent/v1/*` & `/api/a2a/*`)

---

## 1. Quickstart with Python SDK

### Installation & Client Setup
```python
import sys
sys.path.insert(0, "./sdk")

from agentpay import AgentPayClient

client = AgentPayClient(
    base_url="http://localhost:8000",
    api_key="agp_your_agent_api_key_here"
)
```

### Search & Discovery
```python
# Search catalog with price and category constraints
products = client.catalog.search(query="headphones", max_price=5000.0)

for product in products:
    print(f"Product: {product['name']} — ₹{product['price']:,.2f}")
```

### Cart Management & Governed Checkout
```python
# 1. Create a cart
cart = client.cart.create(user_id="customer_101")
cart_id = cart["id"]

# 2. Add product
client.cart.add_item(cart_id=cart_id, product_id=products[0]["id"], quantity=1)

# 3. Request Checkout with Idempotency Key
import uuid
idempotency_key = f"idem_{uuid.uuid4().hex[:12]}"

order = client.checkout.request(
    cart_id=cart_id,
    user_id="customer_101",
    idempotency_key=idempotency_key
)

print(f"Order ID: {order['order']['id']}")
print(f"Status: {order['status']}")
print(f"Requires Human Approval: {order['requires_approval']}")
```

---

## 2. Using Model Context Protocol (MCP)

To connect Claude Desktop, Cursor, or an MCP agent orchestrator:
- Point tool discovery to: `http://localhost:8000/api/mcp/tools`
- Point tool execution to: `http://localhost:8000/api/mcp/call`

Example MCP call:
```json
{
  "tool_name": "evaluate_policy",
  "arguments": {
    "amount": 2500.0,
    "discount_percentage": 10.0
  }
}
```

---

## 3. Best Practices for Agent Developers

1. **Always Supply an Idempotency Key**:
   Include a unique `idempotency_key` (UUID v4) on checkout attempts to avoid duplicate charges on network retries.

2. **Handle Human Approval Gracefully**:
   Transactions exceeding merchant limits or high transaction thresholds return `requires_approval: true`. Your agent should notify the user and monitor `client.orders.get(order_id)` for the transition from `APPROVAL_PENDING` to `APPROVED`.

3. **Respect Rate Limits**:
   Do not hammer endpoints in tight loops. If you receive `VELOCITY_LIMIT_EXCEEDED` or `CIRCUIT_OPEN`, apply exponential backoff.
