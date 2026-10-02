"""Autonomous Checkout Agent Example using AgentPay Python SDK."""

import sys
import os
import uuid

# Add SDK root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sdk")))

from agentpay import AgentPayClient


def run_checkout_agent():
    print("🤖 Initializing Autonomous Purchasing Agent with Governance...")
    client = AgentPayClient(base_url="http://localhost:8000")

    # 1. Search Catalog
    print("🔍 Discovering products...")
    products = client.catalog.search(query="shoes", max_price=3000)
    if not products:
        print("No products found.")
        return

    selected = products[0]
    print(f"✅ Selected: {selected['name']} (₹{selected['price']:,.2f})")

    # 2. Create Cart & Add Item
    print("🛒 Creating shopping cart...")
    cart = client.cart.create(user_id="autonomous_agent_01")
    cart_id = cart["id"]
    print(f"📦 Cart created: {cart_id}")

    client.cart.add_item(cart_id=cart_id, product_id=selected["id"], quantity=1)
    print(f"➕ Added {selected['name']} to cart")

    # 3. Gated Checkout Request
    idempotency_key = f"idem_agent_{uuid.uuid4().hex[:8]}"
    print(f"💳 Requesting gated checkout (Idempotency Key: {idempotency_key})...")
    order_res = client.checkout.request(
        cart_id=cart_id,
        user_id="autonomous_agent_01",
        idempotency_key=idempotency_key,
    )

    print(f"🎯 Checkout Result:")
    print(f"  - Status: {order_res.get('status')}")
    print(f"  - Order ID: {order_res.get('order', {}).get('id')}")
    print(f"  - Requires Human Approval: {order_res.get('requires_approval')}")
    if order_res.get("approval"):
        print(f"  - Approval ID: {order_res['approval']['id']} (Expires in 5 minutes)")


if __name__ == "__main__":
    run_checkout_agent()
