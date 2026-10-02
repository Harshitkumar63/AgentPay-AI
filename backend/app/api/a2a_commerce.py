"""Agent-to-Agent (A2A) Commerce Gateway API (Phase 19).

Supports machine-to-machine interaction between Buyer Agents and Merchant Agents.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.schemas import A2ACommerceRequest, A2ACommerceResponse
from app.services import product_service, cart_service, order_service, negotiation_service, policy_service, audit_service

router = APIRouter(prefix="/a2a", tags=["Agent-to-Agent Commerce"])


class A2ADiscoveryRequest(BaseModel):
    query: str = Field(..., example="wireless noise cancelling headphones")
    max_price: Optional[float] = Field(None, example=5000.0)
    category: Optional[str] = Field(None, example="electronics")
    merchant_id: str = Field("merchant_001", example="merchant_001")


class A2AOfferRequest(BaseModel):
    product_id: str = Field(..., example="prod_001")
    requested_price: float = Field(..., example=2200.0)
    quantity: int = Field(1, example=1)
    merchant_id: str = Field("merchant_001", example="merchant_001")
    agent_id: str = Field("ExternalBuyerBot", example="ExternalBuyerBot")


class A2AAcceptRequest(BaseModel):
    product_id: str = Field(..., example="prod_001")
    final_price: float = Field(..., example=2200.0)
    quantity: int = Field(1, example=1)
    user_id: str = Field("a2a_buyer", example="a2a_buyer")
    merchant_id: str = Field("merchant_001", example="merchant_001")
    agent_id: str = Field("ExternalBuyerBot", example="ExternalBuyerBot")
    idempotency_key: Optional[str] = None


class A2ARejectRequest(BaseModel):
    product_id: str
    reason: str = Field("Price exceeds buyer budget constraints", example="Price exceeds buyer budget constraints")
    merchant_id: str = "merchant_001"
    agent_id: str = "ExternalBuyerBot"


@router.post("/discovery", summary="A2A Product Discovery & Catalog Capabilities")
def a2a_discovery(req: A2ADiscoveryRequest, db: Session = Depends(get_db)):
    """External buyer agent queries catalog specifications and real-time inventory."""
    products = product_service.search_products(
        db,
        query=req.query,
        category=req.category,
        max_price=req.max_price,
        merchant_id=req.merchant_id,
    )
    if not products:
        products = product_service.get_products(db, merchant_id=req.merchant_id, limit=5)

    return {
        "status": "SUCCESS",
        "merchant_id": req.merchant_id,
        "query": req.query,
        "results_count": len(products),
        "candidates": [
            {
                "product_id": p.id,
                "name": p.name,
                "category": p.category,
                "catalog_price": p.price,
                "currency": p.currency,
                "in_stock": p.stock > 0,
                "stock_quantity": p.stock,
                "negotiation_supported": True,
            }
            for p in products
        ],
    }


@router.post("/request", summary="A2A Request Product Quote")
def a2a_request_quote(
    product_id: str = Query(..., example="prod_001"),
    merchant_id: str = Query("merchant_001"),
    db: Session = Depends(get_db),
):
    """Retrieve authoritative quote, specifications, and maximum permissible promotional band."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    policy = policy_service.get_merchant_policy(db, merchant_id)
    max_disc = policy.max_discount_percentage if policy else 15.0

    return {
        "product_id": product.id,
        "name": product.name,
        "base_price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "max_allowable_discount_pct": max_disc,
        "minimum_negotiable_price": round(product.price * (1 - max_disc / 100.0), 2),
    }


@router.post("/offer", summary="A2A Controlled Price Negotiation Offer")
def a2a_propose_offer(req: A2AOfferRequest, db: Session = Depends(get_db)):
    """Buyer agent submits an automated price proposal; merchant policy responds deterministically."""
    res = negotiation_service.propose_negotiation_offer(
        db=db,
        product_id=req.product_id,
        requested_price=req.requested_price,
        merchant_id=req.merchant_id,
        agent_id=req.agent_id,
    )
    return {
        "status": res["status"],
        "product_id": req.product_id,
        "requested_price": req.requested_price,
        "final_offer": res["final_offer"],
        "discount_granted_pct": res["discount_granted_percentage"],
        "message": res["reason"],
    }


@router.post("/accept", summary="A2A Checkout & Order Formulation")
def a2a_accept_and_checkout(req: A2AAcceptRequest, db: Session = Depends(get_db)):
    """Buyer agent accepts offer; initiates cart formation, governance checks, and order creation."""
    # 1. Create cart
    cart = cart_service.get_or_create_cart(db, user_id=req.user_id, merchant_id=req.merchant_id)
    cart_service.add_item(db, cart.id, req.product_id, quantity=req.quantity)

    # 2. Checkout order
    order_res = order_service.create_order(
        db=db,
        cart_id=cart.id,
        user_id=req.user_id,
        merchant_id=req.merchant_id,
        idempotency_key=req.idempotency_key,
        order_type="ai_assisted",
        actor_id=req.agent_id,
        actor_type="ai_agent",
    )

    if order_res.get("error"):
        raise HTTPException(status_code=400, detail=order_res["message"])

    return {
        "status": "ORDER_CREATED",
        "order": order_res.get("order"),
        "requires_approval": order_res.get("requires_approval", False),
        "approval": order_res.get("approval"),
        "policy": order_res.get("policy"),
    }


@router.post("/reject", summary="A2A Negotiation Rejection Telemetry")
def a2a_reject_offer(req: A2ARejectRequest, db: Session = Depends(get_db)):
    """Buyer agent records negotiation termination."""
    audit_service.create_audit_log(
        db=db,
        actor_type="ai_agent",
        actor_id=req.agent_id,
        action="A2A_NEGOTIATION_REJECTED",
        resource_type="product",
        resource_id=req.product_id,
        reason=req.reason,
        result="CANCELLED",
    )
    return {
        "status": "NEGOTIATION_TERMINATED",
        "product_id": req.product_id,
        "message": "Negotiation safely terminated.",
    }


@router.post("/simulate", response_model=A2ACommerceResponse, summary="Simulate Complete 6-Stage A2A Commerce Pipeline")
def simulate_a2a_commerce(
    req: A2ACommerceRequest,
    db: Session = Depends(get_db),
):
    """
    Executes a complete 6-stage machine-to-machine interaction:
    1. Customer AI Agent: Submits goal & discovery query
    2. Merchant Agent: Discovers products and returns options
    3. Customer AI Agent: Evaluates suitability score and selects best value item
    4. Controlled Negotiation: Proposes discount governed by merchant policy
    5. Governance Pipeline: Policy Engine, Risk Scoring, Agent Budget & Trust check
    6. Human Approval / Checkout Orchestration
    """
    steps = []

    # Step 1: Goal
    steps.append({
        "stage": 1,
        "actor": "Customer AI Agent",
        "action": "INITIATE_GOAL",
        "message": f"Autonomous buyer agent initialized with objective: '{req.customer_agent_goal}'",
        "status": "SUCCESS",
    })

    # Step 2: Product discovery
    products = product_service.search_products(db, query="shoes", max_price=3000.0, merchant_id=req.merchant_id)
    if not products:
        products = product_service.get_products(db, merchant_id=req.merchant_id, limit=3)

    selected_product = products[0]
    steps.append({
        "stage": 2,
        "actor": "Merchant Shopping Agent",
        "action": "PRODUCT_DISCOVERY",
        "message": f"Merchant Agent identified {len(products)} candidates. Selected '{selected_product.name}' (₹{selected_product.price:,.2f}) as optimal match.",
        "product_id": selected_product.id,
        "price": selected_product.price,
        "status": "SUCCESS",
    })

    # Step 3: Negotiation
    target_offer_price = round(selected_product.price * 0.92, 2)
    neg_res = negotiation_service.propose_negotiation_offer(
        db=db,
        product_id=selected_product.id,
        requested_price=target_offer_price,
        merchant_id=req.merchant_id,
        agent_id="ShoppingBot",
    )
    steps.append({
        "stage": 3,
        "actor": "AI Negotiation Engine",
        "action": "CONTROLLED_NEGOTIATION",
        "message": f"Customer Agent requested ₹{target_offer_price:,.2f}. Backend Policy validated final offer at ₹{neg_res['final_offer']:,.2f} ({neg_res['status']}).",
        "final_offer": neg_res["final_offer"],
        "status": "SUCCESS",
    })

    # Step 4: Cart and Price Recomputation
    cart = cart_service.get_or_create_cart(db, user_id=req.user_id, merchant_id=req.merchant_id)
    cart_service.add_item(db, cart.id, selected_product.id, quantity=1)
    calc = cart_service.calculate_cart(db, cart.id)

    steps.append({
        "stage": 4,
        "actor": "Cart & Pricing Service",
        "action": "SERVER_PRICING_VALIDATION",
        "message": f"Authoritative server cart recalculated: Subtotal ₹{calc['subtotal']:,.2f}, Total ₹{calc['total']:,.2f}.",
        "status": "SUCCESS",
    })

    # Step 5: Policy & Risk Engine
    pol_res = policy_service.check_purchase_policy(
        db=db,
        merchant_id=req.merchant_id,
        amount=calc["total"],
        action="create_order",
        agent_id="ShoppingBot",
    )
    steps.append({
        "stage": 5,
        "actor": "Policy & Risk Engine",
        "action": "GOVERNANCE_EVALUATION",
        "message": f"Policy check: {pol_res['reason']} (Risk: {pol_res['risk_level']}, Approval Required: {pol_res.get('requires_approval')}).",
        "status": "SUCCESS",
    })

    # Step 6: Order Gated Checkout
    order_res = order_service.create_order(
        db=db,
        cart_id=cart.id,
        user_id=req.user_id,
        merchant_id=req.merchant_id,
        order_type="ai_assisted",
        actor_id="ShoppingBot",
        actor_type="ai_agent",
    )

    steps.append({
        "stage": 6,
        "actor": "Order Service",
        "action": "ORDER_INITIALIZED",
        "message": f"Order {order_res.get('order', {}).get('id')} created. Status: {order_res.get('status')}.",
        "status": "SUCCESS",
    })

    return A2ACommerceResponse(
        steps=steps,
        final_status="ORDER_PENDING_APPROVAL" if order_res.get("requires_approval") else "ORDER_CREATED",
        order_id=order_res.get("order", {}).get("id"),
        amount=calc["total"],
        policy_result=pol_res,
        risk_level=pol_res.get("risk_level", "LOW"),
        approval_required=order_res.get("requires_approval", True),
    )
