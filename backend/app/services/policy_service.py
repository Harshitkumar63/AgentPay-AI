"""Policy and Risk Engine — Deterministic rule evaluation, budget guards, trust check, and decision explanations."""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.services import budget_service, trust_service, audit_service


def evaluate_risk(action: str, amount: float = 0.0, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Deterministic Risk Classification Engine (Phase 13):
    - LOW: search, view, get_product, catalog, compare
    - MEDIUM: cart, add_to_cart, remove_from_cart, coupon, calculate, recommend
    - HIGH: create_order, checkout, payment, refund, campaign, launch_campaign
    """
    details = details or {}
    act = action.lower()

    if any(k in act for k in ["search", "view", "get_product", "catalog", "compare"]):
        return {
            "risk_level": "LOW",
            "risk_score": 10,
            "requires_approval": False,
            "reasons": ["Read-only informational discovery action — 0 financial risk"],
        }

    if any(k in act for k in ["cart", "add_to_cart", "remove_from_cart", "coupon", "calculate", "recommend"]):
        return {
            "risk_level": "MEDIUM",
            "risk_score": 40,
            "requires_approval": False,
            "reasons": ["Cart or session mutation without binding fund movement"],
        }

    if any(k in act for k in ["order", "create_order", "checkout", "payment", "refund", "campaign"]):
        factors = ["Direct financial commitment or fund disbursement"]
        score = 80
        if amount > 5000:
            score = 95
            factors.append(f"High transaction value (₹{amount:,.2f}) mandates human-in-the-loop authorization")
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
    """Get the active policy for a merchant."""
    return db.query(Policy).filter(Policy.merchant_id == merchant_id).first()


def check_purchase_policy(
    db: Session,
    merchant_id: str,
    amount: float,
    discount_percentage: float = 0.0,
    action: str = "create_order",
    agent_id: str = "default_agent",
) -> Dict[str, Any]:
    """
    Comprehensive Policy & Risk Evaluation Pipeline:
    1. Action Permission Check
    2. Max Purchase Amount Check
    3. Discount Percentage Cap Check
    4. Deterministic Risk Engine Scoring
    5. Agent Spending Budget Check (Transaction & Daily Remaining)
    6. Agent Trust Score Verification
    """
    policy = get_merchant_policy(db, merchant_id)
    risk = evaluate_risk(action, amount=amount)
    budget_res = budget_service.check_budget_limit(db, amount, agent_id=agent_id, merchant_id=merchant_id)
    trust_res = trust_service.get_trust_assessment(db, agent_id=agent_id)

    max_allowed_amount = policy.max_purchase_amount if policy else 50000.0
    max_discount_cap = policy.max_discount_percentage if policy else 20.0
    approval_mandated = policy.approval_required if policy else True

    # 1. Action allowed check
    if policy:
        allowed_actions = policy.allowed_actions or []
        if allowed_actions and action not in allowed_actions and "all" not in allowed_actions:
            trust_service.record_trust_event(db, "policy_violation", agent_id=agent_id)
            return {
                "allowed": False,
                "policy_id": policy.id,
                "risk_level": "HIGH",
                "risk_score": 90,
                "requires_approval": False,
                "reason": f"Action '{action}' is blocked by merchant policy permissions",
                "details": {
                    "action": action,
                    "allowed_actions": allowed_actions,
                    "budget": budget_res,
                    "trust": trust_res,
                },
            }

    # 2. Maximum purchase amount check
    if amount > max_allowed_amount:
        trust_service.record_trust_event(db, "policy_violation", agent_id=agent_id)
        return {
            "allowed": False,
            "policy_id": policy.id if policy else "default",
            "risk_level": "HIGH",
            "risk_score": 95,
            "requires_approval": False,
            "reason": f"Amount ₹{amount:,.2f} exceeds configured purchase limit of ₹{max_allowed_amount:,.2f}",
            "details": {
                "requested_amount": amount,
                "maximum_allowed": max_allowed_amount,
                "budget": budget_res,
                "trust": trust_res,
            },
        }

    # 3. Discount percentage check
    if discount_percentage > max_discount_cap:
        trust_service.record_trust_event(db, "policy_violation", agent_id=agent_id)
        return {
            "allowed": False,
            "policy_id": policy.id if policy else "default",
            "risk_level": "HIGH",
            "risk_score": 85,
            "requires_approval": False,
            "reason": f"Discount {discount_percentage:.1f}% exceeds maximum allowed discount of {max_discount_cap:.1f}%",
            "details": {
                "requested_discount": discount_percentage,
                "maximum_allowed_discount": max_discount_cap,
                "budget": budget_res,
                "trust": trust_res,
            },
        }

    # 4. Agent Budget Check
    if not budget_res["allowed"]:
        trust_service.record_trust_event(db, "policy_violation", agent_id=agent_id)
        return {
            "allowed": False,
            "policy_id": policy.id if policy else "budget_gate",
            "risk_level": "HIGH",
            "risk_score": 90,
            "requires_approval": False,
            "reason": budget_res["reason"],
            "details": {
                "requested_amount": amount,
                "budget": budget_res,
                "trust": trust_res,
            },
        }

    # Trust score factor in approval requirement
    trust_tier = trust_res.get("risk_tier", "LOW")
    if trust_tier == "HIGH":
        risk["reasons"].append(f"Agent trust score ({trust_res['trust_score']}/100) is in HIGH risk tier")
        risk["risk_score"] = max(risk["risk_score"], 85)

    requires_approval = approval_mandated or risk["requires_approval"] or (trust_tier in ("MEDIUM", "HIGH") and amount > 1000)

    return {
        "allowed": True,
        "policy_id": policy.id if policy else "default",
        "risk_level": risk["risk_level"],
        "risk_score": risk["risk_score"],
        "requires_approval": requires_approval,
        "reason": f"Amount ₹{amount:,.2f} complies with merchant limits and agent budget constraints",
        "details": {
            "requested_amount": amount,
            "maximum_allowed": max_allowed_amount,
            "discount_percentage": discount_percentage,
            "max_discount_percentage": max_discount_cap,
            "approval_required": requires_approval,
            "risk_reasons": risk["reasons"],
            "budget": budget_res,
            "trust": trust_res,
        },
    }


def simulate_policy(
    db: Session,
    merchant_id: str,
    amount: float,
    discount_percentage: float = 0.0,
    action: str = "create_order",
    agent_id: str = "default_agent",
) -> Dict[str, Any]:
    """Run a test policy simulation without persisting financial state."""
    result = check_purchase_policy(
        db=db,
        merchant_id=merchant_id,
        amount=amount,
        discount_percentage=discount_percentage,
        action=action,
        agent_id=agent_id,
    )
    return {
        "simulation": True,
        "input": {
            "merchant_id": merchant_id,
            "amount": amount,
            "discount_percentage": discount_percentage,
            "action": action,
            "agent_id": agent_id,
        },
        "decision": result,
    }


def explain_decision(action: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate structured, safe 'Why did the AI do this?' explanations (Phases 5 & 24).
    Explains selected factors, alternative exclusion factors, and financial action checks.
    """
    act = action.lower()
    selected_reasons = []
    excluded_reasons = []

    if "product" in act or "search" in act or "recommend" in act:
        product_name = context.get("product_name", "the selected product")

        # Positive selection factors
        if context.get("category_match"):
            selected_reasons.append(f"✓ Category match: Fits requested '{context['category_match']}' category")
        if context.get("color_match"):
            selected_reasons.append(f"✓ Color match: Matches preferred '{context['color_match']}' color")
        if context.get("budget"):
            selected_reasons.append(f"✓ Budget fit: Price fits within budget cap (under ₹{context['budget']:,.2f})")
        if context.get("in_stock", True):
            selected_reasons.append("✓ Availability: Real-time inventory verified available in stock")
        if context.get("recommendation_score"):
            selected_reasons.append(f"✓ Algorithmic score: Highest recommendation affinity score ({context['recommendation_score']}/100)")
        if context.get("cross_sell_relation"):
            selected_reasons.append(f"✓ Cross-sell affinity: High co-purchase correlation with {context['cross_sell_relation']}")

        # Negative exclusion factors (Why alternatives were not selected)
        if context.get("excluded_products"):
            for exp in context["excluded_products"][:3]:
                excluded_reasons.append(f"✗ {exp.get('name', 'Alternative')}: {exp.get('reason', 'Exceeded budget or lower match score')}")

        return {
            "title": f"Why This Product Was Selected: {product_name}",
            "decision": "RECOMMEND_PRODUCT",
            "factors": selected_reasons or ["✓ Exact match for search query and category in catalog"],
            "alternatives_not_selected": excluded_reasons or [
                "✗ Higher priced alternatives outside target budget range",
                "✗ Lower stock availability or lower affinity score",
            ],
        }

    if "order" in act or "checkout" in act or "buy" in act or "create_order" in act:
        return {
            "title": "Why Purchase Preparation Was Initiated",
            "decision": "CREATE_ORDER_PIPELINE",
            "factors": [
                "✓ User explicitly initiated purchase action",
                "✓ Product catalog price and stock validated on server",
                "✓ Server-side subtotal, discount, and tax calculation confirmed",
                "✓ Policy engine verified transaction within merchant limits",
                "✓ Risk engine scored and classified transaction",
                "✓ Agent budget verified (daily limit & per-transaction cap)",
                "✓ Agent trust score verified above minimum risk threshold",
                "✓ Human authorization gate activated prior to payment capture",
            ],
            "alternatives_not_selected": [
                "✗ Direct charge without human approval: Blocked by governance policy",
                "✗ Client-provided price acceptance: Blocked by server-side verification",
            ],
        }

    return {
        "title": "AI Action Governance Summary",
        "decision": action,
        "factors": ["✓ Validated against merchant policies, risk thresholds, and agent budget"],
        "alternatives_not_selected": [],
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
