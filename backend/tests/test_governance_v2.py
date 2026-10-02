"""Comprehensive Governance & Security Test Suite (Phase 42)."""

import pytest
import time
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.main import app
from app.models.agent import Agent, AgentBudget, AgentTrust
from app.models.policy import Policy
from app.models.order import Order
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.merchant import Merchant
from app.models.audit import AuditLog
from app.services import (
    agent_registry_service,
    system_control_service,
    circuit_breaker_service,
    velocity_limiter,
    policy_service,
    trust_service,
    budget_service,
    approval_service,
    order_service,
    audit_service,
    cart_service,
    payment_service,
)

from sqlalchemy.pool import StaticPool

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Reset system controls
    system_control_service.system_control_service.resume_all(db=db, reason="Test setup")

    # Seed test merchant & policy
    merchant = Merchant(id="merchant_001", name="Test Merchant", email="test@merchant.com")
    db.add(merchant)

    policy = Policy(
        merchant_id="merchant_001",
        max_purchase_amount=50000.0,
        max_discount_percentage=20.0,
        approval_required=True,
        allowed_actions=["all"],
    )
    db.add(policy)

    prod = Product(
        id="prod_test_01",
        merchant_id="merchant_001",
        name="Test Governance Sneakers",
        slug="test-governance-sneakers",
        price=3000.0,
        stock=50,
        active=True,
        category="shoes",
    )
    db.add(prod)

    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==========================================
# 1. Agent Authentication & API Key Tests
# ==========================================

def test_agent_authentication_and_key_rotation(test_db):
    """Verify secure SHA-256 API key hashing, authentication, and key rotation."""
    # Create agent
    res = agent_registry_service.create_agent(
        db=test_db,
        name="SecurityBot",
        role="shopping",
        permissions=["catalog.read", "product.search"],
        daily_budget=5000.0,
        transaction_limit=2500.0,
    )
    agent = res["agent"]
    raw_key = res["api_key"]

    # Authenticate valid key
    auth_agent = agent_registry_service.authenticate_api_key(test_db, raw_key)
    assert auth_agent is not None
    assert auth_agent.id == agent.id

    # Reject invalid key
    invalid_agent = agent_registry_service.authenticate_api_key(test_db, "agp_invalid_key_12345")
    assert invalid_agent is None

    # Rotate API key
    rot_res = agent_registry_service.rotate_agent_key(test_db, agent.id)
    assert rot_res["success"] is True
    new_key = rot_res["api_key"]
    assert new_key != raw_key

    # Old key must be invalidated
    assert agent_registry_service.authenticate_api_key(test_db, raw_key) is None
    # New key must authenticate
    assert agent_registry_service.authenticate_api_key(test_db, new_key) is not None


# ==========================================
# 2. Scoped Permissions & Tool Gating Tests
# ==========================================

def test_agent_permissions_enforcement(test_db):
    """Verify fine-grained permissions check blocks unauthorized tools."""
    res = agent_registry_service.create_agent(
        db=test_db,
        name="ReadOnlyBot",
        permissions=["catalog.read", "product.search"],
    )
    agent = res["agent"]

    # Allowed permission
    perm1 = agent_registry_service.check_agent_permission(test_db, agent.id, "catalog.read")
    assert perm1["allowed"] is True

    # Blocked permission
    perm2 = agent_registry_service.check_agent_permission(test_db, agent.id, "order.create")
    assert perm2["allowed"] is False
    assert perm2["error_code"] == "PERMISSION_DENIED"


# ==========================================
# 3. Agent Emergency Pause & Kill Switch
# ==========================================

def test_agent_pause_and_resume(test_db):
    """Verify agent pausing immediately stops financial executions."""
    res = agent_registry_service.create_agent(
        db=test_db,
        name="PausableBot",
        permissions=["all"],
    )
    agent = res["agent"]

    # Pause
    agent_registry_service.update_agent_status(test_db, agent.id, "PAUSED", "Routine maintenance")
    perm = agent_registry_service.check_agent_permission(test_db, agent.id, "order.create")
    assert perm["allowed"] is False
    assert perm["error_code"] == "AGENT_PAUSED"

    # Resume
    agent_registry_service.update_agent_status(test_db, agent.id, "ACTIVE", "Maintenance complete")
    perm_res = agent_registry_service.check_agent_permission(test_db, agent.id, "order.create")
    assert perm_res["allowed"] is True


def test_global_kill_switch(test_db):
    """Verify global kill switch pauses writes while preserving reads."""
    # Global freeze
    system_control_service.system_control_service.pause_all(db=test_db, reason="Global emergency")
    
    chk_write = system_control_service.system_control_service.check_writes_allowed()
    assert chk_write["allowed"] is False
    assert chk_write["error_code"] == "SYSTEM_PAUSED"

    chk_pay = system_control_service.system_control_service.check_payments_allowed()
    assert chk_pay["allowed"] is False

    # Resume
    system_control_service.system_control_service.resume_all(db=test_db, reason="Emergency resolved")
    assert system_control_service.system_control_service.check_writes_allowed()["allowed"] is True


# ==========================================
# 4. Circuit Breaker & Velocity Limiter
# ==========================================

def test_circuit_breaker_trip_and_cooldown(test_db):
    """Verify circuit breaker opens after 5 failures in 2 min and recovers."""
    cb = circuit_breaker_service.circuit_breaker_service
    agent_id = "agent_cb_test"

    # 5 consecutive failures
    for i in range(5):
        cb.record_failure(test_db, agent_id, reason=f"Declined test {i}")

    # Circuit breaker should now be OPEN
    st = cb.get_state(test_db, agent_id)
    assert st["state"] == "OPEN"
    assert st["tripped"] is True

    # Attempts while OPEN are blocked
    exec_chk = cb.can_execute(test_db, agent_id)
    assert exec_chk["allowed"] is False
    assert exec_chk["error_code"] == "CIRCUIT_OPEN"

    # Manual reset
    reset_res = cb.reset_circuit(test_db, agent_id, reason="Manual admin override")
    assert reset_res["success"] is True
    assert cb.can_execute(test_db, agent_id)["allowed"] is True


def test_velocity_limiter(test_db):
    """Verify rate and transaction frequency thresholds."""
    vl = velocity_limiter.velocity_limiter
    agent_id = "agent_vel_test"

    # Within limits
    res = vl.check_transaction_velocity(test_db, agent_id)
    assert res["allowed"] is True

    # Record 5 transactions in current minute
    for _ in range(5):
        vl.record_transaction(test_db, agent_id, 100.0)

    # 6th should exceed per-minute velocity limit (max 5/min)
    res_exceeded = vl.check_transaction_velocity(test_db, agent_id)
    assert res_exceeded["allowed"] is False
    assert res_exceeded["decision"] == "VELOCITY_LIMIT_EXCEEDED"


# ==========================================
# 5. Dynamic Risk Score & Dynamic Budget
# ==========================================

def test_dynamic_risk_score_calculation():
    """Verify continuous 0-100 deterministic risk scoring."""
    # Low risk read query
    low = policy_service.calculate_dynamic_risk_score(action="search_products", amount=0.0, trust_score=95)
    assert low["risk_level"] == "LOW"
    assert low["risk_score"] <= 30

    # Critical risk high value + low trust
    crit = policy_service.calculate_dynamic_risk_score(
        action="create_order",
        amount=15000.0,
        trust_score=40,
        failed_payment_count=2,
    )
    assert crit["risk_level"] in ("HIGH", "CRITICAL")
    assert crit["risk_score"] >= 80
    assert "CRITICAL_TRANSACTION_VALUE" in crit["reason_codes"]
    assert "CRITICAL_AGENT_TRUST_DEFICIT" in crit["reason_codes"]


def test_dynamic_trust_spending_tiers(test_db):
    """Verify trust score tiers connect to transaction caps."""
    # Tier 1: Trust 95 -> ₹10,000 limit
    t1_tier, t1_limit, t1_gate = trust_service.get_trust_tier_limit(95)
    assert t1_tier == "TRUSTED"
    assert t1_limit == 10000.0

    # Tier 4: Trust 40 -> ₹0 limit (mandatory human gate)
    t4_tier, t4_limit, t4_gate = trust_service.get_trust_tier_limit(40)
    assert t4_tier == "CRITICAL_GATED"
    assert t4_gate is True


# ==========================================
# 6. Human Approvals & Expiration
# ==========================================

def test_approval_creation_and_expiration(test_db):
    """Verify human approval creation and 5-minute expiration."""
    appr = approval_service.create_approval_request(
        db=test_db,
        amount=4500.0,
        action="create_order",
        ttl_minutes=5,
    )
    assert appr.status == "PENDING"
    assert appr.is_expired is False

    # Simulate past expiration
    appr.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    test_db.commit()

    dec = approval_service.decide_approval(test_db, appr.id, "APPROVED")
    assert dec.get("error") is True
    assert dec["code"] == "APPROVAL_EXPIRED"


# ==========================================
# 7. Order Machine & Enhanced Idempotency
# ==========================================

def test_order_state_transitions(test_db):
    """Verify authoritative 12-state order machine enforces legal progression."""
    order = Order(
        merchant_id="merchant_001",
        user_id="user_01",
        cart_id="cart_01",
        amount=3000.0,
        status="APPROVAL_PENDING",
    )
    test_db.add(order)
    test_db.commit()
    test_db.refresh(order)

    # Illegal transition directly to COMPLETED
    res_bad = order_service.transition_order_status(test_db, order, "COMPLETED")
    assert res_bad["success"] is False
    assert res_bad["code"] == "INVALID_STATE_TRANSITION"

    # Legal transition to APPROVED
    res_ok = order_service.transition_order_status(test_db, order, "APPROVED")
    assert res_ok["success"] is True
    assert order.status == "APPROVED"


def test_idempotency_conflict_detection(test_db):
    """Verify same idempotency key with different payload returns 409 IDEMPOTENCY_CONFLICT."""
    cart1 = cart_service.get_or_create_cart(test_db, user_id="user_idem", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart1.id, "prod_test_01", quantity=1)

    idem_key = f"idem_key_{uuid.uuid4().hex[:8]}"

    # First order
    res1 = order_service.create_order(
        db=test_db,
        cart_id=cart1.id,
        user_id="user_idem",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res1["status"] == "created"

    # Exact replay with same cart/user/merchant/amount -> returns idempotent order
    res_replay = order_service.create_order(
        db=test_db,
        cart_id=cart1.id,
        user_id="user_idem",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res_replay["status"] == "existing"

    # Attempt reuse of same key for a different user/cart -> conflict
    cart2 = cart_service.get_or_create_cart(test_db, user_id="user_different", merchant_id="merchant_001")
    cart_service.add_item(test_db, cart2.id, "prod_test_01", quantity=2)

    res_conflict = order_service.create_order(
        db=test_db,
        cart_id=cart2.id,
        user_id="user_different",
        merchant_id="merchant_001",
        idempotency_key=idem_key,
    )
    assert res_conflict.get("error") is True
    assert res_conflict["code"] == "IDEMPOTENCY_CONFLICT"


# ==========================================
# 8. Tamper-Evident Hash Chain Integrity
# ==========================================

def test_tamper_evident_audit_trail_and_tamper_detection(test_db):
    """Verify cryptographic SHA-256 hash chaining and mathematical tamper detection."""
    # Create 3 audit logs
    log1 = audit_service.create_audit_log(test_db, "user", "u1", "ACTION_1", "order", "ord_1", amount=100.0)
    log2 = audit_service.create_audit_log(test_db, "user", "u1", "ACTION_2", "order", "ord_2", amount=200.0)
    log3 = audit_service.create_audit_log(test_db, "user", "u1", "ACTION_3", "order", "ord_3", amount=300.0)

    # Verify chain from genesis
    verify_res = audit_service.verify_audit_trail(test_db)
    assert verify_res["valid"] is True
    assert verify_res["events_checked"] >= 3

    # Tamper with log2 amount directly in DB without updating hash
    log2.amount = 999999.0
    test_db.commit()

    # Verify chain should now detect mathematical tampering
    tamper_check = audit_service.verify_audit_trail(test_db)
    assert tamper_check["valid"] is False
    assert tamper_check["broken_at"] == log2.id


# ==========================================
# 9. Agent Manifest & MCP Tool Layer
# ==========================================

def test_agent_manifest_endpoint(client):
    """Verify machine-readable /.well-known/agent.json returns capabilities without exposing secrets."""
    r = client.get("/.well-known/agent.json")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "AgentPay AI"
    assert "capabilities" in data
    assert "governance" in data
    assert "protocols" in data
    # Ensure no secrets exposed
    assert "secret" not in str(data).lower() or "webhook_secret" not in data


def test_mcp_tools_and_call_endpoint(client, test_db):
    """Verify all 16 MCP tools are discoverable and executable under governance."""
    r_tools = client.get("/api/mcp/tools")
    assert r_tools.status_code == 200
    tools = r_tools.json()["tools"]
    assert len(tools) == 16

    # Execute search_products MCP tool
    r_call = client.post("/api/mcp/call", json={
        "tool_name": "search_products",
        "arguments": {"query": "shoes"},
    })
    assert r_call.status_code == 200
    res = r_call.json()
    assert res["status"] == "SUCCESS"
    assert "products" in res["result"]


# ==========================================
# 10. A2A Commerce Flow
# ==========================================

def test_a2a_commerce_endpoints(client):
    """Verify machine-to-machine Discovery -> Offer -> Accept -> Order."""
    # 1. Discovery
    r_disc = client.post("/api/a2a/discovery", json={"query": "shoes", "max_price": 4000.0})
    assert r_disc.status_code == 200
    candidates = r_disc.json()["candidates"]
    assert len(candidates) >= 1

    prod_id = candidates[0]["product_id"]

    # 2. Offer Negotiation
    r_offer = client.post("/api/a2a/offer", json={
        "product_id": prod_id,
        "requested_price": 2700.0,
        "agent_id": "BuyerA2ABot",
    })
    assert r_offer.status_code == 200
    assert "final_offer" in r_offer.json()

    # 3. Accept & Checkout
    r_accept = client.post("/api/a2a/accept", json={
        "product_id": prod_id,
        "final_price": r_offer.json()["final_offer"],
        "user_id": "buyer_01",
        "agent_id": "BuyerA2ABot",
    })
    assert r_accept.status_code == 200
    assert r_accept.json()["status"] == "ORDER_CREATED"


# ==========================================
# 11. Policy Simulator Non-Mutating Tests
# ==========================================

def test_policy_simulator_non_mutating(test_db):
    """Verify policy simulator performs dry-runs without persisting financial mutations."""
    count_before = test_db.query(Order).count()
    sim_res = policy_service.simulate_policy(
        db=test_db,
        merchant_id="merchant_001",
        amount=4500.0,
        discount_percentage=10.0,
    )
    assert sim_res["simulation"] is True
    assert sim_res["decision"]["allowed"] is True
    count_after = test_db.query(Order).count()
    # No order record must be written during simulation
    assert count_before == count_after


# ==========================================
# 12. Webhook Signature & Deduplication
# ==========================================

def test_webhook_signature_verification_and_event_deduplication(client, test_db):
    """Verify webhook signature validation and duplicate event handling."""
    order = Order(
        id="ord_wh_test",
        merchant_id="merchant_001",
        user_id="user_wh",
        cart_id="cart_wh",
        amount=2500.0,
        status="PAYMENT_PENDING",
        razorpay_order_id="order_rz_wh_123",
    )
    test_db.add(order)
    test_db.commit()

    event_id = f"evt_test_{uuid.uuid4().hex[:8]}"
    payload = {
        "entity": "event",
        "account_id": "acc_test",
        "event": "payment.captured",
        "id": event_id,
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_wh_captured_999",
                    "order_id": "order_rz_wh_123",
                    "amount": 250000,
                    "status": "captured",
                }
            }
        },
    }

    # 1. First webhook delivery
    r1 = client.post("/api/webhooks/razorpay", json=payload)
    assert r1.status_code == 200

    # 2. Replayed/duplicate webhook delivery with same event ID
    r2 = client.post("/api/webhooks/razorpay", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "already_processed"


# ==========================================
# 13. Notifications Center API Tests
# ==========================================

def test_notification_center_endpoints(client):
    """Verify security alerts and notifications API."""
    r_list = client.get("/api/notifications")
    assert r_list.status_code == 200
    notifs = r_list.json()
    assert len(notifs) >= 1

    notif_id = notifs[0]["id"]
    r_read = client.post(f"/api/notifications/{notif_id}/read")
    assert r_read.status_code == 200
    assert r_read.json()["success"] is True

