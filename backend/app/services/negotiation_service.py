"""Controlled AI Negotiation Engine (Part 12).

Enforces backend merchant policies and margin bounds on price negotiations.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.policy import Policy
from app.services import policy_service, product_service, audit_service


def propose_negotiation_offer(
    db: Session,
    product_id: str,
    requested_price: float,
    merchant_id: str = "merchant_001",
    agent_id: str = "ShoppingBot",
) -> Dict[str, Any]:
    """
    Controlled negotiation pipeline:
    LLM Proposal -> Backend Policy Validation -> Maximum Discount Cap -> Margin Check -> Authoritative Final Offer.
    """
    product = product_service.get_product(db, product_id)
    if not product:
        return {
            "error": True,
            "message": "Product not found",
            "status": "REJECTED",
        }

    policy = policy_service.get_merchant_policy(db, merchant_id)
    # Default 10% max negotiation discount cap if not configured
    max_discount_pct = min(15.0, policy.max_discount_percentage if policy else 10.0)

    current_price = float(product.price)
    max_allowed_discount_amount = round(current_price * (max_discount_pct / 100.0), 2)
    min_allowed_price = round(current_price - max_allowed_discount_amount, 2)

    # Requested discount percentage
    requested_discount_pct = max(0.0, round(((current_price - requested_price) / current_price) * 100.0, 1))

    if requested_price >= current_price:
        final_offer = current_price
        status = "ACCEPTED"
        discount_granted = 0.0
        reason = f"Requested price ₹{requested_price:,.2f} is at or above catalog price (₹{current_price:,.2f})."
    elif requested_price >= min_allowed_price:
        final_offer = requested_price
        status = "ACCEPTED"
        discount_granted = requested_discount_pct
        reason = f"Accepted requested price ₹{requested_price:,.2f} ({requested_discount_pct}% discount within {max_discount_pct}% policy limit)."
    else:
        final_offer = min_allowed_price
        status = "COUNTER_OFFER"
        discount_granted = max_discount_pct
        reason = f"Requested price ₹{requested_price:,.2f} exceeds merchant maximum allowed discount ({max_discount_pct}%). Best authorized counter-offer is ₹{min_allowed_price:,.2f}."

    # Audit log
    audit_service.create_audit_log(
        db,
        actor_type="ai_agent",
        actor_id=agent_id,
        action="AI_NEGOTIATION_PROPOSAL",
        resource_type="product",
        resource_id=product.id,
        amount=final_offer,
        currency="INR",
        reason=reason,
        policy_result="ALLOWED" if status in ("ACCEPTED", "COUNTER_OFFER") else "BLOCKED",
        result="SUCCESS",
        metadata_extra={
            "current_price": current_price,
            "requested_price": requested_price,
            "final_offer": final_offer,
            "max_discount_pct": max_discount_pct,
            "discount_granted_pct": discount_granted,
        },
    )

    return {
        "product_id": product.id,
        "product_name": product.name,
        "current_price": current_price,
        "requested_price": requested_price,
        "max_allowed_discount": max_allowed_discount_amount,
        "max_discount_percentage": max_discount_pct,
        "minimum_margin_price": min_allowed_price,
        "final_offer": final_offer,
        "discount_granted_percentage": discount_granted,
        "status": status,
        "reason": reason,
        "currency": product.currency or "INR",
    }
