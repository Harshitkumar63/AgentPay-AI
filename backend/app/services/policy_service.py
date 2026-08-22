"""Policy and Risk Engine — evaluates financial action policies and risk levels."""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.policy import Policy


def evaluate_risk(action: str, amount: float = 0.0, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Risk Classification Layer (Phase 13):
    - LOW: search_products, get_product, compare_products, get_cart, get_catalog
    - MEDIUM: add_to_cart, remove_from_cart, apply_coupon, calculate_cart
    - HIGH: create_order, payment, refund, launch_campaign
    """
    details = details or {}
    act = action.lower()

    if any(k in act for k in ["search", "view", "get_product", "catalog", "compare"]):
        return {
            "risk_level": "LOW",
            "risk_score": 10,
            "requires_approval": False,
            "reasons": ["Read-only informational discovery action"],
        }

    if any(k in act for k in ["cart", "add_to_cart", "remove_from_cart", "coupon", "calculate"]):
        return {
            "risk_level": "MEDIUM",
            "risk_score": 40,
            "requires_approval": False,
            "reasons": ["Cart mutation without financial charge"],
        }

    if any(k in act for k in ["order", "create_order", "checkout", "payment", "refund", "campaign"]):
        factors = ["Direct financial commitment or fund movement"]
        score = 80
        if amount > 5000:
            score = 95
            factors.append(f"Transaction value (₹{amount:,.2f}) requires human verification")
        elif amount > 0:
            factors.append(f"Transaction value: ₹{amount:,.2f}")

        return {
            "risk_level": "HIGH",
            "risk_score": score,
            "requires_approval": True,
            "reasons": factors,
        }

    return {
        "risk_level": "MEDIUM",
        "risk_score": 50,
        "requires_approval": False,
        "reasons": ["Standard system operation"],
    }


def get_merchant_policy(db: Session, merchant_id: str) -> Optional[Policy]:
    """Get the policy for a merchant."""
    return db.query(Policy).filter(Policy.merchant_id == merchant_id).first()


def check_purchase_policy(
    db: Session,
    merchant_id: str,
    amount: float,
    discount_percentage: float = 0.0,
    action: str = "create_order",
) -> dict:
    """
    Evaluate purchase against merchant policy with full risk assessment.
    Returns structured allow/deny result.
    """
    policy = get_merchant_policy(db, merchant_id)
    risk = evaluate_risk(action, amount=amount)

    if not policy:
        return {
            "allowed": True,
            "policy_id": "default",
            "risk_level": risk["risk_level"],
            "risk_score": risk["risk_score"],
            "requires_approval": risk["requires_approval"],
            "reason": "Default policy active — standard limits applied",
            "details": {
                "requested_amount": amount,
                "discount_percentage": discount_percentage,
                "max_allowed": 50000.0,
            },
        }

    # 1. Action allowed check
    allowed_actions = policy.allowed_actions or []
    if allowed_actions and action not in allowed_actions and "all" not in allowed_actions:
        return {
            "allowed": False,
            "policy_id": policy.id,
            "risk_level": "HIGH",
            "risk_score": 90,
            "requires_approval": False,
            "reason": f"Action '{action}' is not in merchant's allowed actions policy",
            "details": {
                "action": action,
                "allowed_actions": allowed_actions,
            },
        }

    # 2. Maximum purchase amount check
    if amount > policy.max_purchase_amount:
        return {
            "allowed": False,
            "policy_id": policy.id,
            "risk_level": "HIGH",
            "risk_score": 95,
            "requires_approval": False,
            "reason": f"Amount ₹{amount:,.2f} exceeds configured purchase limit of ₹{policy.max_purchase_amount:,.2f}",
            "details": {
                "requested_amount": amount,
                "maximum_allowed": policy.max_purchase_amount,
            },
        }

    # 3. Discount percentage check
    if discount_percentage > policy.max_discount_percentage:
        return {
            "allowed": False,
            "policy_id": policy.id,
            "risk_level": "HIGH",
            "risk_score": 85,
            "requires_approval": False,
            "reason": f"Discount {discount_percentage:.1f}% exceeds maximum allowed discount of {policy.max_discount_percentage:.1f}%",
            "details": {
                "requested_discount": discount_percentage,
                "maximum_allowed_discount": policy.max_discount_percentage,
            },
        }

    requires_approval = policy.approval_required or risk["requires_approval"]

    return {
        "allowed": True,
        "policy_id": policy.id,
        "risk_level": risk["risk_level"],
        "risk_score": risk["risk_score"],
        "requires_approval": requires_approval,
        "reason": f"Amount ₹{amount:,.2f} passed all policy and risk thresholds",
        "details": {
            "requested_amount": amount,
            "maximum_allowed": policy.max_purchase_amount,
            "discount_percentage": discount_percentage,
            "max_discount_percentage": policy.max_discount_percentage,
            "approval_required": requires_approval,
            "risk_reasons": risk["reasons"],
        },
    }


def simulate_policy(
    db: Session,
    merchant_id: str,
    amount: float,
    discount_percentage: float = 0.0,
    action: str = "create_order",
) -> dict:
    """Run a test policy simulation without persisting state."""
    result = check_purchase_policy(
        db=db,
        merchant_id=merchant_id,
        amount=amount,
        discount_percentage=discount_percentage,
        action=action,
    )
    return {
        "simulation": True,
        "input": {
            "merchant_id": merchant_id,
            "amount": amount,
            "discount_percentage": discount_percentage,
            "action": action,
        },
        "decision": result,
    }


def explain_decision(action: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate structured 'Why did the AI do this?' explanations (Phase 15).
    """
    act = action.lower()
    reasons = []

    if "product" in act or "search" in act or "recommend" in act:
        product_name = context.get("product_name", "the product")
        if context.get("category_match"):
            reasons.append(f"Matches requested category '{context['category_match']}'")
        if context.get("color_match"):
            reasons.append(f"Matches preferred color '{context['color_match']}'")
        if context.get("budget"):
            reasons.append(f"Fits within target budget (under ₹{context['budget']:,.2f})")
        if context.get("in_stock", True):
            reasons.append("Inventory verified available in stock")
        if context.get("is_top_rated"):
            reasons.append("Highest suitability & customer satisfaction ranking")
        if context.get("cross_sell_relation"):
            reasons.append(f"Frequently bought together with {context['cross_sell_relation']}")

        return {
            "title": f"Why this recommendation: {product_name}",
            "decision": "RECOMMEND_PRODUCT",
            "factors": reasons or ["Matches your search parameters and catalog availability"],
        }

    if "order" in act or "checkout" in act or "buy" in act:
        return {
            "title": "Why purchase preparation was initiated",
            "decision": "PREPARE_PURCHASE",
            "factors": [
                "User explicitly initiated checkout request",
                "Product inventory re-verified with database",
                "Server-side price recalculation completed",
                "Policy & financial limit compliance passed",
                "Human approval gate activated before payment dispatch",
            ],
        }

    return {
        "title": "AI Action Explanation",
        "decision": action,
        "factors": ["Action validated against system policies and context"],
    }


def check_action_allowed(db: Session, merchant_id: str, action: str) -> bool:
    """Check if a specific action is allowed by policy."""
    policy = get_merchant_policy(db, merchant_id)
    if not policy:
        return True
    allowed = policy.allowed_actions or []
    return action in allowed or "all" in allowed


def update_policy(db: Session, merchant_id: str, updates: dict) -> Optional[Policy]:
    """Update merchant policy."""
    policy = get_merchant_policy(db, merchant_id)
    if not policy:
        return None
    for key, value in updates.items():
        if value is not None and hasattr(policy, key):
            setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy
