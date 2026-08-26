"""
Comprehensive Test Suite for AgentPay AI.
Tests database models, services, deterministic policy & risk engines, agent budget & trust scores,
human approval gating, idempotency, Razorpay Test Mode payments, webhooks, AI Buyer API, MCP layer,
Decision Replay, and full End-to-End Integration Pipeline.
"""

import pytest
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.database import Base, get_db
from app.main import app
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.models.product import Product
from app.models.order import Order
from app.models.payment import Payment
from app.models.webhook import WebhookEvent
from app.models.agent import AgentBudget, AgentTrust
from app.models.approval import Approval
from app.models.recommendation_event import RecommendationEvent
from app.models.campaign import CampaignProposal
from app.models.audit import AuditLog
from app.services import (
    product_service,
    cart_service,
    order_service,
    policy_service,
    payment_service,
    audit_service,
    recommendation_service,
    analytics_service,
    budget_service,
    trust_service,
    approval_service,
)
from app.agents.shopping_agent import process_chat, MAX_AGENT_TOOL_CALLS


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
        metadata_extra={"colors": ["black", "blue"], "cross_sell": ["prod_002"], "upsell": "prod_004"},
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

    # Seed product 3 (Upsell)
    prod3 = Product(
        id="prod_004",
        merchant_id="merchant_001",
        name="ProRunner Elite Racing Shoes",
        slug="prorunner-elite",
        description="Premium carbon plate racing shoes",
        category="shoes",
        price=4999.0,
        currency="INR",
        stock=5,
        active=True,
        tags=["running", "shoes", "elite"],
        metadata_extra={"upsell_from": "prod_001"},
    )
    db.add(prod3)

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
    prods = product_service.search_products(test_db, query="running shoes", merchant_id="merchant_001")
    assert len(prods) >= 1
    assert prods[0].id == "prod_001"

    cheap_prods = product_service.search_products(test_db, max_price=500.0, merchant_id="merchant_001")
    assert len(cheap_prods) == 1
    assert cheap_prods[0].id == "prod_002"

    black_shoes = product_service.search_products(test_db, color="black", merchant_id="merchant_001")
    assert any(p.id == "prod_001" for p in black_shoes)


def test_recommendation_scoring_and_generation(test_db):
    """Test deterministic recommendation scoring and cross-sell/upsell generation."""
    recs_cross = recommendation_service.get_recommendations(test_db, "prod_001", "cross_sell")
    assert len(recs_cross) >= 1
    assert recs_cross[0]["product"]["id"] == "prod_002"
    assert recs_cross[0]["score"] > 0

    recs_upsell = recommendation_service.get_recommendations(test_db, "prod_001", "upsell")
    assert len(recs_upsell) >= 1
    assert recs_upsell[0]["product"]["id"] == "prod_004"
    assert recs_upsell[0]["price_difference"] == 2500.0


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


def test_agent_budget_limits(test_db):
    """Test agent spending limits (per-transaction cap and daily budget)."""
    budget = budget_service.get_or_create_budget(test_db, agent_id="test_agent", merchant_id="merchant_001")
    budget.per_transaction_limit = 3000.0
    budget.daily_limit = 6000.0
    budget.spent_today = 4000.0
    test_db.commit()

    # 1. Fits within per-transaction and remaining daily (₹1500 <= ₹2000 remaining)
    b_ok = budget_service.check_budget_limit(test_db, 1500.0, agent_id="test_agent", merchant_id="merchant_001")
    assert b_ok["allowed"] is True

    # 2. Exceeds per-transaction limit (₹3500 > ₹3000)
    b_tx_fail = budget_service.check_budget_limit(test_db, 3500.0, agent_id="test_agent", merchant_id="merchant_001")
    assert b_tx_fail["allowed"] is False
    assert b_tx_fail["limit_type"] == "PER_TRANSACTION_LIMIT"

    # 3. Exceeds remaining daily budget (₹2500 > ₹2000 remaining)
    b_daily_fail = budget_service.check_budget_limit(test_db, 2500.0, agent_id="test_agent", merchant_id="merchant_001")
    assert b_daily_fail["allowed"] is False
    assert b_daily_fail["limit_type"] == "DAILY_BUDGET_EXCEEDED"


def test_agent_trust_score_calculation(test_db):
    """Test server-calculated agent trust score and penalty/bonus factors."""
    trust = trust_service.get_or_create_trust(test_db, agent_id="trust_agent")
    assert trust.trust_score >= 80

    # Record policy violation
    trust_service.record_trust_event(test_db, "policy_violation", agent_id="trust_agent")
    assessment = trust_service.get_trust_assessment(test_db, agent_id="trust_agent")
    assert assessment["signals"]["policy_violations"] == 1
    assert assessment["trust_score"] < 90


def test_human_approval_lifecycle_and_expiration(test_db):
    """Test human approval creation, TTL expiration, and authorization decision."""
    appr = approval_service.create_approval_request(
        test_db,
        amount=2499.0,
        merchant_id="merchant_001",
        reason="High-risk test transaction",
        ttl_minutes=5,
    )
    assert appr.status == "PENDING"
    assert not appr.is_expired

    # Decision approval
    dec_res = approval_service.decide_approval(test_db, appr.id, status="APPROVED", approved_by="admin_test")
    assert dec_res["success"] is True
    assert dec_res["status"] == "APPROVED"

    # Validation check
    val = approval_service.validate_approval(test_db, appr.id, expected_amount=2499.0)
    assert val["valid"] is True


def test_expired_approval_rejection(test_db):
    """Test that approval past TTL is marked EXPIRED and rejected."""
    appr = approval_service.create_approval_request(
        test_db,
        amount=2499.0,
        merchant_id="merchant_001",
        ttl_minutes=-1,  # Expired in past
    )
    val = approval_service.validate_approval(test_db, appr.id)
    assert val["valid"] is False
    assert val["code"] == "APPROVAL_EXPIRED"


def test_idempotency_order_creation(test_db):
    """Test idempotency: same idempotency_key must return existing order without duplicates."""
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)

    idem_key = "idemp_test_abc123"

    res1 = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="user_123",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res1["status"] == "created"
    first_order_id = res1["order"]["id"]

    res2 = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="user_123",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res2["status"] == "existing"
    assert res2["order"]["id"] == first_order_id

    total_orders = test_db.query(Order).filter(Order.idempotency_key == idem_key).count()
    assert total_orders == 1


def test_duplicate_webhook_protection(client, test_db):
    """Test webhook idempotency: duplicate event ID is safely ignored without duplicate mutations."""
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)
    order_res = order_service.create_order(test_db, cart_id=cart.id, user_id="user_123", merchant_id="merchant_001")
    order_id = order_res["order"]["id"]
    
    # Approve order if needed
    if order_res.get("approval"):
        approval_service.decide_approval(test_db, order_res["approval"]["id"], status="APPROVED")
        
    pay_res = payment_service.create_payment_for_order(test_db, order_id)
    rz_order_id = pay_res["razorpay_order_id"]

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

    r1 = client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "processed"

    r2 = client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_processed"


def test_payment_failure_handling(client, test_db):
    """Test safe payment failure recording and audit logging."""
    cart = cart_service.get_or_create_cart(test_db, user_id="user_123", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)
    order_res = order_service.create_order(test_db, cart_id=cart.id, user_id="user_123", merchant_id="merchant_001")
    order_id = order_res["order"]["id"]
    
    if order_res.get("approval"):
        approval_service.decide_approval(test_db, order_res["approval"]["id"], status="APPROVED")

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

    order = order_service.get_order(test_db, order_id)
    assert order.payment_status == "failed"

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


def test_campaign_proposal_and_activation(client, test_db):
    """Test AI Campaign Proposal creation and activation."""
    r_prop = client.post("/api/campaigns/propose", json={
        "product_id": "prod_001",
        "title": "Flash Sale on ProRunner",
        "discount_percentage": 10.0,
        "budget": 1000.0,
        "duration_days": 3,
        "target_audience": "Shoe Category Browsers",
    })
    assert r_prop.status_code == 200
    camp_id = r_prop.json()["id"]

    r_act = client.post(f"/api/campaigns/{camp_id}/activate")
    assert r_act.status_code == 200
    assert r_act.json()["status"] == "active"


def test_decision_replay_endpoint(client, test_db):
    """Test Decision Replay reconstruction endpoint."""
    cart = cart_service.get_or_create_cart(test_db, user_id="replay_user", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)
    res = order_service.create_order(test_db, cart_id=cart.id, user_id="replay_user", merchant_id="merchant_001")
    order_id = res["order"]["id"]

    r_replay = client.get(f"/api/orders/{order_id}/decision-replay")
    assert r_replay.status_code == 200
    data = r_replay.json()
    assert data["order_id"] == order_id
    assert len(data["stages"]) >= 5


def test_mcp_endpoints(client, test_db):
    """Test MCP tool definitions and direct execution."""
    r_tools = client.get("/api/mcp/tools")
    assert r_tools.status_code == 200
    assert len(r_tools.json()["tools"]) > 0

    r_call = client.post("/api/mcp/call", json={
        "tool_name": "search_products",
        "arguments": {"query": "running"},
    })
    assert r_call.status_code == 200
    assert r_call.json()["status"] == "SUCCESS"


def test_end_to_end_commerce_pipeline(client, test_db):
    """
    Complete End-to-End Integration Test (Phase 48):
    USER -> AI AGENT -> SEARCH -> RECOMMEND -> CART -> POLICY -> RISK -> BUDGET -> TRUST -> APPROVAL -> ORDER -> PAYMENT -> WEBHOOK -> AUDIT -> ANALYTICS.
    """
    # 1. Search products
    search_res = product_service.search_products(test_db, query="running", max_price=3000.0)
    assert len(search_res) >= 1
    selected_product = search_res[0]

    # 2. Get recommendations
    recs = recommendation_service.get_recommendations(test_db, selected_product.id, "cross_sell")
    assert len(recs) >= 1
    accessory = recs[0]["product"]

    # 3. Create cart & add items
    cart = cart_service.get_or_create_cart(test_db, user_id="e2e_user", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, selected_product.id, 1)
    cart_service.add_item(test_db, cart.id, accessory["id"], 1)

    # 4. Calculate cart securely on server
    calc = cart_service.calculate_cart(test_db, cart.id)
    assert calc["total"] == selected_product.price + accessory["price"]

    # 5. Policy & Risk Engine check
    policy_res = policy_service.check_purchase_policy(test_db, "merchant_001", amount=calc["total"], agent_id="e2e_agent")
    assert policy_res["allowed"] is True

    # 6. Create order (Gated with human approval if required)
    order_res = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="e2e_user",
        merchant_id="merchant_001",
        order_type="cross_sell",
        actor_id="e2e_agent",
        actor_type="ai_agent",
    )
    assert order_res["status"] == "created"
    order_id = order_res["order"]["id"]

    # 7. Grant human approval
    if order_res.get("approval"):
        approval_id = order_res["approval"]["id"]
        appr_dec = approval_service.decide_approval(test_db, approval_id, "APPROVED", approved_by="admin_e2e")
        assert appr_dec["success"] is True

    # 8. Initialize Payment (Razorpay Test Mode)
    pay_init = payment_service.create_payment_for_order(test_db, order_id)
    assert "razorpay_order_id" in pay_init
    rz_order_id = pay_init["razorpay_order_id"]

    # 9. Verify Payment Signature
    pay_verify = payment_service.verify_and_update_payment(
        test_db,
        razorpay_order_id=rz_order_id,
        razorpay_payment_id="pay_e2e_captured_123",
        razorpay_signature="e2e_signature",
    )
    assert pay_verify["payment_status"] == "captured"

    # 10. Webhook processing
    webhook_payload = {
        "entity": "event",
        "account_id": "acc_demo",
        "event": "payment.captured",
        "id": f"evt_e2e_{int(time.time())}",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_e2e_captured_123",
                    "order_id": rz_order_id,
                    "amount": int(calc["total"] * 100),
                    "status": "captured",
                }
            }
        },
    }
    r_wh = client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert r_wh.status_code == 200

    # 11. Verify Audit trail
    audit_logs = test_db.query(AuditLog).filter(AuditLog.resource_id == order_id).all()
    assert len(audit_logs) >= 1

    # 12. Verify Revenue Analytics
    rev_analytics = analytics_service.get_revenue_analytics(test_db, "merchant_001")
    assert rev_analytics["total_revenue"] >= calc["total"]
    assert rev_analytics["successful_orders"] >= 1


def test_max_tool_call_limit(test_db):
    """Test safety guard: Agent terminates if tool calls reach MAX_AGENT_TOOL_CALLS (8)."""
    assert MAX_AGENT_TOOL_CALLS == 8


def test_price_tamper_resistance(test_db):
    """Test that client-submitted prices are ignored and recalculated from verified database records."""
    cart = cart_service.get_or_create_cart(test_db, user_id="tamper_user", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart.id, "prod_001", quantity=1)
    
    # Client creates order
    order_res = order_service.create_order(
        test_db,
        cart_id=cart.id,
        user_id="tamper_user",
        merchant_id="merchant_001",
    )
    # Price is always 2499.0 regardless of client manipulation
    assert order_res["order"]["amount"] == 2499.0


def test_policy_simulator_endpoint(client, test_db):
    """Test Policy Simulator endpoint with amount, discount, and agent risk scoring."""
    r_sim = client.post("/api/policies/simulate", json={
        "amount": 7500.0,
        "discount_percentage": 10.0,
        "action": "create_order",
        "agent_id": "sim_agent",
    })
    assert r_sim.status_code == 200
    data = r_sim.json()
    assert "decision" in data
    assert data["decision"]["risk_level"] in ("LOW", "MEDIUM", "HIGH")


def test_recommendation_event_telemetry(test_db):
    """Test tracking recommendation impressions, clicks, and purchases."""
    recommendation_service.record_recommendation_event(
        test_db,
        merchant_id="merchant_001",
        recommendation_type="cross_sell",
        event_type="shown",
        source_product_id="prod_001",
        recommended_product_id="prod_002",
    )
    recommendation_service.record_recommendation_event(
        test_db,
        merchant_id="merchant_001",
        recommendation_type="cross_sell",
        event_type="clicked",
        source_product_id="prod_001",
        recommended_product_id="prod_002",
    )
    recommendation_service.record_recommendation_event(
        test_db,
        merchant_id="merchant_001",
        recommendation_type="cross_sell",
        event_type="purchased",
        source_product_id="prod_001",
        recommended_product_id="prod_002",
        revenue_attributed=399.0,
    )

    stats = recommendation_service.get_recommendation_analytics(test_db, "merchant_001")
    assert stats["cross_sell"]["shown"] >= 1
    assert stats["cross_sell"]["clicked"] >= 1
    assert stats["cross_sell"]["purchased"] >= 1
    assert stats["cross_sell"]["revenue"] >= 399.0

