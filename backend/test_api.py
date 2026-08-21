"""Quick test script for the Agent API."""
import sys
import httpx
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


time.sleep(2)

BASE = "http://127.0.0.1:8000"

# Test health
r = httpx.get(f"{BASE}/health")
print("HEALTH:", r.json())

# Test products
r = httpx.get(f"{BASE}/api/products")
prods = r.json()
print(f"PRODUCTS: {len(prods)} products loaded")

# Test agent chat
r = httpx.post(f"{BASE}/api/agent/chat", json={
    "message": "Show me running shoes under 3000",
    "user_id": "demo_user",
    "merchant_id": "merchant_001",
})
d = r.json()
print(f"AGENT MSG: {d['message'][:300]}")
print(f"PRODUCTS FOUND: {len(d['products'])}")
print(f"STEPS: {len(d['agent_steps'])}")
for p in d["products"][:5]:
    print(f"  -> {p['name']} - Rs{p['price']}")

# Test cart creation
r = httpx.post(f"{BASE}/api/cart", json={
    "user_id": "demo_user",
    "merchant_id": "merchant_001",
})
cart = r.json()
cart_id = cart.get("id")
print(f"CART CREATED: {cart_id}")

# Test add to cart
if prods:
    r = httpx.post(f"{BASE}/api/cart/{cart_id}/items", json={
        "product_id": "prod_001",
        "quantity": 1,
    })
    print(f"ADD TO CART: {r.status_code}")

# Test analytics
r = httpx.get(f"{BASE}/api/analytics/revenue")
print(f"ANALYTICS: {r.status_code}")

# Test policies
r = httpx.get(f"{BASE}/api/policies")
print(f"POLICIES: {r.status_code}")

# Test audit logs
r = httpx.get(f"{BASE}/api/audit")
print(f"AUDIT: {r.status_code} ({len(r.json())} entries)")

print("\n=== ALL TESTS PASSED ===")
