"""AgentPayClient — Python Client for Governed Agentic Commerce."""

import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, List


class CatalogClient:
    def __init__(self, client: "AgentPayClient"):
        self._client = client

    def search(self, query: str, max_price: Optional[float] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        payload = {"query": query}
        if max_price is not None:
            payload["max_price"] = max_price
        if category:
            payload["category"] = category
        res = self._client._post("/api/agent/v1/search", payload)
        return res.get("results", [])

    def get_product(self, product_id: str) -> Dict[str, Any]:
        return self._client._get(f"/api/agent/v1/catalog/{product_id}")

    def list_all(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        path = "/api/agent/v1/catalog"
        if category:
            path += f"?category={urllib.parse.quote(category)}"
        res = self._client._get(path)
        return res.get("products", [])


class CartClient:
    def __init__(self, client: "AgentPayClient"):
        self._client = client

    def create(self, user_id: str = "ai_agent_buyer") -> Dict[str, Any]:
        return self._client._post("/api/agent/v1/cart", {"user_id": user_id})

    def get(self, cart_id: str) -> Dict[str, Any]:
        return self._client._get(f"/api/agent/v1/cart/{cart_id}")

    def add_item(self, cart_id: str, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        return self._client._post(f"/api/agent/v1/cart/{cart_id}/items", {
            "product_id": product_id,
            "quantity": quantity,
        })


class CheckoutClient:
    def __init__(self, client: "AgentPayClient"):
        self._client = client

    def request(
        self,
        cart_id: str,
        user_id: str = "ai_agent_buyer",
        merchant_id: str = "merchant_001",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "cart_id": cart_id,
            "user_id": user_id,
            "merchant_id": merchant_id,
            "order_type": "ai_assisted",
        }
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        return self._client._post("/api/agent/v1/checkout", payload)


class OrdersClient:
    def __init__(self, client: "AgentPayClient"):
        self._client = client

    def get(self, order_id: str) -> Dict[str, Any]:
        return self._client._get(f"/api/agent/v1/orders/{order_id}")


class AgentPayClient:
    """
    Official Python Client for AgentPay AI.
    
    Usage:
        client = AgentPayClient(base_url="http://localhost:8000", api_key="agp_...")
        products = client.catalog.search(query="running shoes", max_price=3000)
        cart = client.cart.create()
        client.cart.add_item(cart_id=cart["id"], product_id=products[0]["id"])
        order = client.checkout.request(cart_id=cart["id"])
    """

    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.catalog = CatalogClient(self)
        self.cart = CartClient(self)
        self.checkout = CheckoutClient(self)
        self.orders = OrdersClient(self)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["X-Agent-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=self._headers(), method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
