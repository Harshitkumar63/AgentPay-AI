"""Basic Autonomous Buyer Agent Example using AgentPay Python SDK."""

import sys
import os

# Add SDK root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sdk")))

from agentpay import AgentPayClient


def run_basic_agent():
    print("🤖 Initializing Autonomous Shopping Agent...")
    client = AgentPayClient(base_url="http://localhost:8000")

    # 1. Search Catalog
    print("🔍 Searching catalog for 'running shoes' under ₹3,000...")
    products = client.catalog.search(query="running shoes", max_price=3000)
    print(f"✅ Found {len(products)} matching candidate(s):")
    for p in products:
        print(f"  - [{p['id']}] {p['name']} — ₹{p['price']:,.2f}")

    if not products:
        print("No products found.")
        return

    # 2. Inspect Details
    selected = products[0]
    details = client.catalog.get_product(selected["id"])
    print(f"\n📦 Selected Product Details: {details['name']} (Stock: {details['stock']})")


if __name__ == "__main__":
    run_basic_agent()
