"""
Comprehensive test suite for AgentPay AI.
Tests database models, services, policy & risk engine, idempotency, payments, webhooks, and AI Buyer API.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.main import app
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.models.product import Product
from app.models.order import Order
from app.models.payment import Payment
from app.models.webhook import WebhookEvent
from app.services import (
    product_service,
    cart_service,
    order_service,
    policy_service,
    payment_service,
    audit_service,
    recommendation_service,
    analytics_service,
)


from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session()


    # Seed merchant
    merchant = Merchant(
        id="merchant_001",
        name="UrbanCart",
        email="merchant@urbancart.com",
        currency="INR",
        description="Test store",
    )
    db.add(merchant)

    # Seed policy
    policy = Policy(
        id="pol_test_001",
        merchant_id="merchant_001",
        max_purchase_amount=5000.0,
        max_discount_percentage=15.0,
        approval_required=True,
        auto_refund_enabled=True,
        allowed_actions=["search", "view", "cart", "create_order", "recommend", "get_payment_status"],
    )
    db.add(policy)

    # Seed product 1
    prod = Product(
        id="prod_001",
        merchant_id="merchant_001",
        name="ProRunner X1 Running Shoes",
        slug="prorunner-x1",
        description="Running shoes in black and blue",
        category="shoes",
        price=2499.0,
        currency="INR",
        stock=10,
        active=True,
        tags=["running", "shoes", "black"],
        metadata_extra={"colors": ["black", "blue"], "cross_sell": ["prod_002"]},
    )
    db.add(prod)

    # Seed product 2
    prod2 = Product(
        id="prod_002",
        merchant_id="merchant_001",
        name="Running Socks (3-Pack)",
        slug="running-socks",
        description="Comfort moisture-wicking athletic socks",
        category="accessories",
        price=399.0,
        currency="INR",
        stock=50,
        active=True,
        tags=["running", "socks", "accessories"],
        metadata_extra={},
    )
    db.add(prod2)

    db.commit()
    yield db
    db.close()


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Tests ─────────────────────────────────────────────────────────────

def test_product_search_and_filters(test_db):
    """Test natural language search and price/color filtering."""
    # Keyword search
    prods = product_service.search_products(test_db, query="running shoes", merchant_id="merchant_001")
    assert len(prods) >= 1
    assert prods[0].id == "prod_001"

    # Price budget filter
    cheap_prods = product_service.search_products(test_db, max_price=500.0, merchant_id="merchant_001")
    assert len(cheap_prods) == 1
    assert cheap_prods[0].id == "prod_002"

    # Color filter
    black_shoes = product_service.search_products(test_db, color="black", merchant_id="merchant_001")
    assert any(p.id == "prod_001" for p in black_shoes)


def test_inventory_check_insufficient(test_db):
    """Test inventory gating: requesting more than available stock is rejected."""
    inv_ok = product_service.check_inventory(test_db, "prod_001", quantity=5)
    assert inv_ok["available"] is True

    inv_fail = product_service.check_inventory(test_db, "prod_001", quantity=25)
    assert inv_fail["available"] is False
    assert "Insufficient stock" in inv_fail["reason"]


def test_cart_operations_and_calculations(test_db):
    """Test cart lifecycle and server-side recalculations."""
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    assert cart.id is not None

    item = cart_service.add_item(test_db, cart.id, "prod_001", quantity=2)
    assert item is not None

    details = cart_service.get_cart_details(test_db, cart.id)
    assert details["item_count"] == 2
    assert details["total"] == 4998.0

    calc = cart_service.calculate_cart(test_db, cart.id)
    assert calc["total"] == 4998.0


def test_policy_engine_limits_and_discounts(test_db):
    """Test policy gating for transaction value and maximum discount limits."""
    # Under limit (₹2499 <= ₹5000) -> Allowed
    res1 = policy_service.check_purchase_policy(test_db, "merchant_001", amount=2499.0, discount_percentage=10.0)
    assert res1["allowed"] is True
    assert res1["requires_approval"] is True
    assert res1["risk_level"] in ("LOW", "MEDIUM", "HIGH")

    # Over limit (₹7500 > ₹5000) -> Blocked
    res2 = policy_service.check_purchase_policy(test_db, "merchant_001", amount=7500.0, discount_percentage=10.0)
    assert res2["allowed"] is False
    assert "exceeds" in res2["reason"].lower()

    # Excessive discount (30% > 15%) -> Blocked
    res3 = policy_service.check_purchase_policy(test_db, "merchant_001", amount=2000.0, discount_percentage=30.0)
    assert res3["allowed"] is False
    assert "discount" in res3["reason"].lower()


def test_idempotency_order_creation(test_db):
    """Test idempotency: same idempotency_key must return existing order without duplicates."""
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)

    idem_key = "idemp_test_abc123"

    # First request
    res1 = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="user_123",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res1["status"] == "created"
    first_order_id = res1["order"]["id"]

    # Second request with SAME idempotency key
    res2 = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="user_123",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res2["status"] == "existing"
    assert res2["order"]["id"] == first_order_id

    # Verify database has only ONE order
    total_orders = test_db.query(Order).filter(Order.idempotency_key == idem_key).count()
    assert total_orders == 1


def test_duplicate_webhook_protection(client, test_db):
    """Test webhook idempotency: duplicate event ID is safely ignored without duplicate mutations."""
    # Create order first
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)
    order_res = order_service.create_order(test_db, cart_id=cart.id, user_id="user_123", merchant_id="merchant_001")
    order_id = order_res["order"]["id"]
    pay_res = payment_service.create_payment_for_order(test_db, order_id)
    rz_order_id = pay_res["razorpay_order_id"]

    # Simulated webhook payload
    webhook_payload = {
        "entity": "event",
        "account_id": "acc_demo",
        "event": "payment.captured",
        "id": "evt_unique_1001",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_001",
                    "order_id": rz_order_id,
                    "amount": 249900,
                    "status": "captured",
                }
            }
        },
    }

    # First webhook post
    r1 = client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "processed"

    # Duplicate webhook post with SAME event ID
    r2 = client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_processed"


def test_payment_failure_handling(client, test_db):
    """Test safe payment failure recording and audit logging."""
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)
    order_res = order_service.create_order(test_db, cart_id=cart.id, user_id="user_123", merchant_id="merchant_001")
    order_id = order_res["order"]["id"]
    pay_res = payment_service.create_payment_for_order(test_db, order_id)
    rz_order_id = pay_res["razorpay_order_id"]

    fail_payload = {
        "entity": "event",
        "account_id": "acc_demo",
        "event": "payment.failed",
        "id": "evt_fail_999",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_failed_123",
                    "order_id": rz_order_id,
                    "amount": 249900,
                    "status": "failed",
                    "error_code": "CARD_DECLINED",
                    "error_description": "Card issuer declined transaction",
                }
            }
        },
    }

    resp = client.post("/api/webhooks/razorpay", json=fail_payload)
    assert resp.status_code == 200

    # Order payment status must be marked failed
    order = order_service.get_order(test_db, order_id)
    assert order.payment_status == "failed"

    # Payment record must have error code
    pay = test_db.query(Payment).filter(Payment.order_id == order_id).first()
    assert pay.status == "failed"
    assert pay.error_code == "CARD_DECLINED"


def test_product_comparison(test_db):
    """Test product comparison engine with pros, cons, and suitability picking."""
    comp = product_service.compare_products(test_db, ["prod_001", "prod_002"])
    assert comp["compared_count"] == 2
    assert "recommendation" in comp
    assert comp["recommendation"]["recommended_product_id"] in ("prod_001", "prod_002")


def test_ai_buyer_api_endpoints(client, test_db):
    """Test the machine-to-machine AI Buyer API (v1)."""
    # 1. Tool specifications
    r_tools = client.get("/api/agent/v1/tools")
    assert r_tools.status_code == 200
    assert "tools" in r_tools.json()

    # 2. Catalog
    r_cat = client.get("/api/agent/v1/catalog")
    assert r_cat.status_code == 200
    assert r_cat.json()["total_products"] >= 2

    # 3. Search
    r_search = client.post("/api/agent/v1/search", json={"query": "running", "max_price": 3000})
    assert r_search.status_code == 200
    assert r_search.json()["count"] >= 1

    # 4. Cart & Item
    r_cart = client.post("/api/agent/v1/cart")
    assert r_cart.status_code == 200
    cart_id = r_cart.json()["id"]

    r_add = client.post(f"/api/agent/v1/cart/{cart_id}/items", json={"product_id": "prod_001", "quantity": 1})
    assert r_add.status_code == 200
    assert r_add.json()["item_count"] == 1


def test_merchant_ai_copilot(client, test_db):
    """Test Merchant AI Copilot analytical Q&A."""
    r_copilot = client.post("/api/analytics/copilot", json={"query": "Why did revenue drop this month?"})
    assert r_copilot.status_code == 200
    data = r_copilot.json()
    assert "answer" in data
    assert "metrics_used" in data
    assert len(data["suggested_actions"]) > 0


def test_policy_simulator_endpoint(client, test_db):
    """Test Policy Simulator endpoint."""
    r_sim = client.post("/api/policies/simulate", json={"amount": 7500.0, "discount_percentage": 5.0})
    assert r_sim.status_code == 200
    data = r_sim.json()
    assert data["decision"]["allowed"] is False
    assert "exceeds" in data["decision"]["reason"].lower()
