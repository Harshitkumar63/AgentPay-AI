"""AI Buyer API (v1) — Dedicated machine-to-machine commerce API for external AI agents."""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import product_service, cart_service, order_service, payment_service, policy_service
from app.schemas.schemas import (
    CatalogResponse,
    CatalogProduct,
    BuyerSearchRequest,
    BuyerCheckoutRequest,
    CartRead,
    CartItemCreate,
    OrderRead,
    PaymentRead,
)
from app.models.merchant import Merchant
from app.models.product import Product

router = APIRouter(prefix="/agent/v1", tags=["AI Buyer API (v1)"])


@router.get("/tools", summary="MCP / External Agent Tool Specifications")
def get_tool_specifications():
    """Returns machine-readable MCP / OpenAI tool definitions for external agents."""
    from app.agents.shopping_agent import TOOL_DEFINITIONS
    return {
        "version": "1.0.0",
        "protocol": "Model Context Protocol / OpenAI Tool Calling",
        "description": "AgentPay AI Commerce Interface for Autonomous Agents",
        "tools": TOOL_DEFINITIONS,
    }


@router.get("/catalog", response_model=CatalogResponse, summary="Get AI-Readable Catalog")
def get_ai_catalog(
    merchant_id: str = Query(default="merchant_001"),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Retrieve full catalog structured specifically for consumption by LLM and autonomous agents."""
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    merchant_dict = {
        "id": merchant.id if merchant else merchant_id,
        "name": merchant.name if merchant else "UrbanCart",
        "currency": merchant.currency if merchant else "INR",
    }

    products = product_service.get_products(db, merchant_id=merchant_id, limit=100)
    if category:
        products = [p for p in products if p.category.lower() == category.lower()]

    catalog_products = []
    for p in products:
        catalog_products.append(
            CatalogProduct(
                id=p.id,
                name=p.name,
                description=p.description,
                category=p.category,
                price=p.price,
                currency=p.currency,
                availability=p.stock > 0 and p.active,
                stock=p.stock,
                tags=p.tags or [],
                purchase_allowed=p.stock > 0 and p.active,
                metadata_extra=p.metadata_extra or {},
            )
        )

    return CatalogResponse(
        merchant=merchant_dict,
        products=catalog_products,
        total_products=len(catalog_products),
    )


@router.get("/catalog/{product_id}", summary="Get Product Details for AI Agent")
def get_ai_catalog_product(product_id: str, db: Session = Depends(get_db)):
    """Retrieve a single factual product representation with verified stock and specifications."""
    product = product_service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "in_stock": product.stock > 0 and product.active,
        "tags": product.tags or [],
        "specifications": product.metadata_extra or {},
    }


@router.post("/search", summary="Search Catalog for AI Agent")
def search_ai_catalog(req: BuyerSearchRequest, db: Session = Depends(get_db)):
    """Natural language or filtered product discovery for autonomous agents."""
    products = product_service.search_products(
        db=db,
        query=req.query,
        category=req.category,
        max_price=req.max_price,
        min_price=req.min_price,
        color=req.color,
        merchant_id=req.merchant_id,
    )

    return {
        "query": req.query,
        "count": len(products),
        "results": [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "currency": p.currency,
                "stock": p.stock,
                "available": p.stock > 0,
                "tags": p.tags or [],
                "image_url": p.image_url,
            }
            for p in products[:req.limit]
        ],
    }


@router.post("/cart", summary="Create Cart for AI Agent")
def create_ai_cart(
    user_id: str = "ai_agent_buyer",
    merchant_id: str = "merchant_001",
    db: Session = Depends(get_db),
):
    """Initialize a dedicated shopping cart for an autonomous agent session."""
    cart = cart_service.get_or_create_cart(db, user_id=user_id, merchant_id=merchant_id)
    return cart_service.get_cart_details(db, cart.id)


@router.get("/cart/{cart_id}", summary="Get AI Cart Details")
def get_ai_cart(cart_id: str, db: Session = Depends(get_db)):
    """Fetch recalculate cart state for external agent."""
    details = cart_service.get_cart_details(db, cart_id)
    if "error" in details:
        raise HTTPException(status_code=404, detail="Cart not found")
    return details


@router.post("/cart/{cart_id}/items", summary="Add Item to AI Cart")
def add_item_to_ai_cart(cart_id: str, item: CartItemCreate, db: Session = Depends(get_db)):
    """Add product to agent cart with verified database pricing."""
    cart_item = cart_service.add_item(db, cart_id=cart_id, product_id=item.product_id, quantity=item.quantity)
    if not cart_item:
        raise HTTPException(status_code=400, detail="Could not add item to cart (insufficient stock or invalid product)")
    return cart_service.get_cart_details(db, cart_id)


@router.post("/checkout", summary="Execute Gated Checkout for AI Agent")
def checkout_ai_cart(req: BuyerCheckoutRequest, db: Session = Depends(get_db)):
    """
    Executes full checkout pipeline for autonomous agents:
    Cart Validation -> Stock Check -> Server-Side Price Recomputation -> Policy & Risk Engine -> Order Creation.
    """
    result = order_service.create_order(
        db=db,
        cart_id=req.cart_id,
        user_id=req.user_id,
        merchant_id=req.merchant_id,
        idempotency_key=req.idempotency_key,
        order_type=req.order_type,
        actor_id="ai_buyer_api",
        actor_type="ai_agent",
    )

    if result.get("error"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": result.get("code", "CHECKOUT_FAILED"),
                "message": result.get("message", "Checkout rejected"),
                "policy": result.get("policy"),
            },
        )

    # Initialize payment order if order created
    order_data = result.get("order", {})
    payment_init = None
    if order_data.get("id"):
        payment_init = payment_service.create_payment_for_order(db, order_data["id"])

    return {
        "status": result.get("status", "created"),
        "order": order_data,
        "requires_approval": result.get("requires_approval", True),
        "policy": result.get("policy", {}),
        "payment": payment_init,
    }


@router.get("/orders/{order_id}", summary="Get Order Status for AI Agent")
def get_ai_order(order_id: str, db: Session = Depends(get_db)):
    """Retrieve full order details and fulfillment status."""
    order = order_service.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_service._order_to_dict(order)


@router.get("/payments/{payment_id}", summary="Get Payment Status for AI Agent")
def get_ai_payment(payment_id: str, db: Session = Depends(get_db)):
    """Retrieve verified payment state."""
    from app.models.payment import Payment
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "razorpay_payment_id": payment.razorpay_payment_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "method": payment.method,
        "error_code": payment.error_code,
        "error_description": payment.error_description,
    }
