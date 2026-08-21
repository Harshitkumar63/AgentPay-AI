"""
Comprehensive test suite for AgentPay AI.
Tests database models, services, policies, payments, webhooks, and agent tools.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.models.product import Product
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
from app.schemas.schemas import ProductCreate


@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
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
        merchant_id="merchant_001",
        max_purchase_amount=50000.0,
        max_discount_percentage=20.0,
        approval_required=True,
        auto_refund_enabled=True,
        allowed_actions=["search", "view", "cart", "purchase", "recommend"],
    )
    db.add(policy)

    # Seed product
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
        metadata_extra={"cross_sell": ["prod_002"]},
    )
    db.add(prod)

    prod2 = Product(
        id="prod_002",
        merchant_id="merchant_001",
        name="Running Socks",
        slug="running-socks",
        description="Comfort socks",
        category="accessories",
        price=399.0,
        currency="INR",
        stock=50,
        active=True,
        tags=["running", "socks"],
        metadata_extra={},
    )
    db.add(prod2)

    db.commit()
    yield db
    db.close()


def test_product_search(test_db):
    prods = product_service.search_products(test_db, query="running shoes", merchant_id="merchant_001")
    assert len(prods) >= 1
    assert prods[0].id == "prod_001"


def test_cart_operations(test_db):
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    assert cart.id is not None

    item = cart_service.add_item(test_db, cart.id, "prod_001", quantity=2)
    assert item is not None

    details = cart_service.get_cart_details(test_db, cart.id)
    assert details["item_count"] == 2
    assert details["total"] == 4998.0

    calc = cart_service.calculate_cart(test_db, cart.id)
    assert calc["total"] == 4998.0


def test_policy_engine(test_db):
    # Within limit
    res1 = policy_service.check_purchase_policy(test_db, "merchant_001", 10000.0)
    assert res1["allowed"] is True
    assert res1["requires_approval"] is True

    # Exceeding limit (max is 50000)
    res2 = policy_service.check_purchase_policy(test_db, "merchant_001", 60000.0)
    assert res2["allowed"] is False
    assert "exceeds" in res2["reason"].lower()


def test_order_creation_and_audit_trail(test_db):
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)

    order_result = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="user_123",
        merchant_id="merchant_001",
        order_type="ai_assisted",
    )

    assert "error" not in order_result
    order = order_result["order"]
    assert order["amount"] == 2499.0
    assert order_result["requires_approval"] is True

    # Check audit log was recorded
    logs = audit_service.get_audit_logs(test_db)
    assert len(logs) > 0
    actions = [l.action for l in logs]
    assert "CREATE_ORDER" in actions or "ORDER_CREATED" in actions


def test_payment_service_demo_flow(test_db):
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)

    order_res = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="user_123",
        merchant_id="merchant_001",
    )
    order_id = order_res["order"]["id"]

    # Create payment
    pay_res = payment_service.create_payment_for_order(test_db, order_id)
    assert "error" not in pay_res
    rzp_order_id = pay_res["razorpay_order_id"]

    # Verify payment
    verify_res = payment_service.verify_and_update_payment(
        test_db,
        razorpay_order_id=rzp_order_id,
        razorpay_payment_id="pay_demo_test_123",
        razorpay_signature="demo_signature",
    )
    assert verify_res["success"] is True
    assert verify_res["payment_status"] == "captured"


def test_recommendations(test_db):
    cross_sells = recommendation_service.get_recommendations(
        test_db, product_id="prod_001", recommendation_type="cross_sell", merchant_id="merchant_001"
    )
    assert isinstance(cross_sells, list)
    assert len(cross_sells) >= 1
    assert cross_sells[0]["product"]["id"] == "prod_002"
    assert cross_sells[0]["type"] == "cross_sell"



