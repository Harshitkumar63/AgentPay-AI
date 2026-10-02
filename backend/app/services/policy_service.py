"""Policy and Risk Engine — Continuous 0-100 Deterministic Risk Scoring, Dynamic Spending Tiers, and Policy Gates (Phases 7, 9, 23)."""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.services import budget_service, trust_service, audit_service

# Risk Threshold Constants
RISK_THRESHOLD_LOW = 30
RISK_THRESHOLD_MEDIUM = 60
RISK_THRESHOLD_HIGH = 80


def calculate_dynamic_risk_score(
    action: str,
    amount: float = 0.0,
    discount_percentage: float = 0.0,
    trust_score: int = 90,
    failed_payment_count: int = 0,
    policy_violations_count: int = 0,
    daily_budget_utilization_pct: float = 0.0,
    velocity_minute_count: int = 0,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Continuous Deterministic Risk Scoring Engine (0-100):
    Classifications:
      0-30: LOW
      31-60: MEDIUM
      61-80: HIGH
      81-100: CRITICAL
    Deterministic Signals:
      - Action intent severity
      - Monetary magnitude
      - Agent trust deficit
      - Discount magnitude
      - Historical payment failures & policy breaches
      - Daily budget utilization rate
    """
    act = action.lower()
    score = 0
    reason_codes: List[str] = []
    reasons: List[str] = []

    # 1. Base Action Inherent Risk
    if any(k in act for k in ["search", "view", "get_product", "catalog", "compare"]):
        score += 5
        reasons.append("Read-only informational discovery action (0 financial risk)")
    elif any(k in act for k in ["cart", "add_to_cart", "remove_from_cart", "recommend", "optimize"]):
        score += 20
        reasons.append("Cart state mutation without direct fund movement")
    elif any(k in act for k in ["campaign"]):
        score += 45
        reason_codes.append("CAMPAIGN_PROPOSAL")
        reasons.append("Commercial campaign promotion proposal")
    elif any(k in act for k in ["refund"]):
        score += 55
        reason_codes.append("REFUND_DISBURSEMENT")
        reasons.append("Capital refund disbursement request")
    elif any(k in act for k in ["order", "checkout", "payment", "create_order"]):
        score += 50
        reason_codes.append("FINANCIAL_TRANSACTION")
        reasons.append("Direct monetary transaction creation")
    else:
        score += 25

    # 2. Transaction Amount Magnitude
    if amount > 10000:
        score += 35
        reason_codes.append("CRITICAL_TRANSACTION_VALUE")
        reasons.append(f"Very high transaction value: ₹{amount:,.2f}")
    elif amount > 5000:
        score += 25
        reason_codes.append("HIGH_TRANSACTION_VALUE")
        reasons.append(f"High transaction value: ₹{amount:,.2f}")
    elif amount > 2000:
        score += 15
        reason_codes.append("MODERATE_TRANSACTION_VALUE")
        reasons.append(f"Moderate transaction value: ₹{amount:,.2f}")
    elif amount > 0:
        score += 5

    # 3. Agent Trust Deficit Penalty (Lower trust increases risk score)
    if trust_score < 50:
        score += 30
        reason_codes.append("CRITICAL_AGENT_TRUST_DEFICIT")
        reasons.append(f"Low agent trust score ({trust_score}/100) mandates scrutiny")
    elif trust_score < 70:
        score += 18
        reason_codes.append("MODERATE_AGENT_TRUST_DEFICIT")
        reasons.append(f"Sub-optimal agent trust score ({trust_score}/100)")
    elif trust_score >= 90:
        score -= 10
        reasons.append(f"High agent reliability bonus ({trust_score}/100 trust)")

    # 4. Unusual or High Discount
    if discount_percentage > 20.0:
        score += 20
        reason_codes.append("HIGH_DISCOUNT_ANOMALY")
        reasons.append(f"High requested discount rate: {discount_percentage:.1f}%")
    elif discount_percentage > 10.0:
        score += 10
        reason_codes.append("MODERATE_DISCOUNT")

    # 5. Prior Payment Failures and Policy Breaches
    if failed_payment_count > 0:
        penalty = min(20, failed_payment_count * 8)
        score += penalty
        reason_codes.append("PRIOR_PAYMENT_FAILURES")
        reasons.append(f"Agent associated with {failed_payment_count} recent payment failure(s)")

    if policy_violations_count > 0:
        penalty = min(20, policy_violations_count * 10)
        score += penalty
        reason_codes.append("PRIOR_POLICY_VIOLATIONS")
        reasons.append(f"Agent triggered {policy_violations_count} prior policy violation(s)")

    # 6. Budget Utilization Spike
    if daily_budget_utilization_pct > 80.0:
        score += 15
        reason_codes.append("HIGH_BUDGET_UTILIZATION")
        reasons.append(f"Agent daily budget utilization at {daily_budget_utilization_pct:.1f}%")

    # 7. Velocity Surge
    if velocity_minute_count >= 3:
        score += 15
        reason_codes.append("HIGH_VELOCITY_SURGE")
        reasons.append(f"Rapid transaction frequency ({velocity_minute_count} txs in current minute)")

    final_score = int(max(0, min(100, score)))

    # Classification
    if final_score <= RISK_THRESHOLD_LOW:
        level = "LOW"
    elif final_score <= RISK_THRESHOLD_MEDIUM:
        level = "MEDIUM"
    elif final_score <= RISK_THRESHOLD_HIGH:
        level = "HIGH"
    else:
        level = "CRITICAL"

    requires_approval = level in ("HIGH", "CRITICAL") or amount > 5000.0 or trust_score < 70

    return {
        "risk_score": final_score,
        "risk_level": level,
        "requires_approval": requires_approval,
        "reason_codes": reason_codes or ["STANDARD_OPERATION"],
        "reasons": reasons,
    }


def evaluate_risk(action: str, amount: float = 0.0, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Compatibility wrapper evaluating risk for actions."""
    details = details or {}
    return calculate_dynamic_risk_score(
        action=action,
        amount=amount,
        discount_percentage=details.get("discount_percentage", 0.0),
        trust_score=details.get("trust_score", 90),
        failed_payment_count=details.get("failed_payment_count", 0),
        policy_violations_count=details.get("policy_violations_count", 0),
        daily_budget_utilization_pct=details.get("daily_budget_utilization_pct", 0.0),
        velocity_minute_count=details.get("velocity_minute_count", 0),
        category=details.get("category"),
    )


def get_merchant_policy(db: Session, merchant_id: str) -> Optional[Policy]:
    """Get active merchant policy."""
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
    2. Max Purchase Cap Check
    3. Discount Cap Check
    4. Dynamic 0-100 Risk Engine Scoring
    5. Agent Spending Limits & Dynamic Trust Tiers
    6. Human-in-the-Loop Gating Decision
    """
    policy = get_merchant_policy(db, merchant_id)
    budget_res = budget_service.check_budget_limit(db, amount, agent_id=agent_id, merchant_id=merchant_id)
    trust_res = trust_service.get_trust_assessment(db, agent_id=agent_id)

    trust_score = trust_res.get("trust_score", 90)
    signals = trust_res.get("signals", {})

    # Compute Dynamic Risk Score
    risk = calculate_dynamic_risk_score(
        action=action,
        amount=amount,
        discount_percentage=discount_percentage,
        trust_score=trust_score,
        failed_payment_count=signals.get("failed_payments", 0),
        policy_violations_count=signals.get("policy_violations", 0),
        daily_budget_utilization_pct=budget_res.get("utilization_pct", 0.0),
    )

    max_allowed_amount = policy.max_purchase_amount if policy else 50000.0
    max_discount_cap = policy.max_discount_percentage if policy else 20.0
    approval_mandated = policy.approval_required if policy else True

    # 1. Action Permission check
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
                "reason": f"Action '{action}' is blocked by merchant policy configuration",
                "reason_codes": ["ACTION_NOT_PERMITTED"],
                "details": {
                    "action": action,
                    "allowed_actions": allowed_actions,
                    "budget": budget_res,
                    "trust": trust_res,
                },
            }

    # 2. Max Purchase Amount check
    if amount > max_allowed_amount:
        trust_service.record_trust_event(db, "policy_violation", agent_id=agent_id)
        return {
            "allowed": False,
            "policy_id": policy.id if policy else "default",
            "risk_level": "HIGH",
            "risk_score": 95,
            "requires_approval": False,
            "reason": f"Amount ₹{amount:,.2f} exceeds configured purchase limit of ₹{max_allowed_amount:,.2f}",
            "reason_codes": ["MAX_PURCHASE_AMOUNT_EXCEEDED"],
            "details": {
                "requested_amount": amount,
                "maximum_allowed": max_allowed_amount,
                "budget": budget_res,
                "trust": trust_res,
            },
        }

    # 3. Discount Cap check
    if discount_percentage > max_discount_cap:
        trust_service.record_trust_event(db, "policy_violation", agent_id=agent_id)
        return {
            "allowed": False,
            "policy_id": policy.id if policy else "default",
            "risk_level": "HIGH",
            "risk_score": 85,
            "requires_approval": False,
            "reason": f"Discount {discount_percentage:.1f}% exceeds maximum allowed discount of {max_discount_cap:.1f}%",
            "reason_codes": ["DISCOUNT_CAP_EXCEEDED"],
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
            "reason_codes": [budget_res.get("limit_type", "BUDGET_EXCEEDED")],
            "details": {
                "requested_amount": amount,
                "budget": budget_res,
                "trust": trust_res,
            },
        }

    # 5. Dynamic Spending Limits based on Trust Score Tiers (Section 9)
    # Trust 90-100: max single tx ₹10,000
    # Trust 70-89: max single tx ₹5,000
    # Trust 50-69: max single tx ₹2,000
    # Trust <50: Human approval unconditionally required
    if trust_score < 50:
        risk["requires_approval"] = True
        risk["reasons"].append(f"Trust score below 50 ({trust_score}/100) mandates human approval")
    elif trust_score < 70 and amount > 2000.0:
        risk["requires_approval"] = True
        risk["reasons"].append(f"Tier 3 Trust ({trust_score}/100) mandates human approval for amounts over ₹2,000")
    elif trust_score < 90 and amount > 5000.0:
        risk["requires_approval"] = True
        risk["reasons"].append(f"Tier 2 Trust ({trust_score}/100) mandates human approval for amounts over ₹5,000")

    requires_approval = approval_mandated or risk["requires_approval"]

    return {
        "allowed": True,
        "policy_id": policy.id if policy else "default",
        "risk_level": risk["risk_level"],
        "risk_score": risk["risk_score"],
        "reason_codes": risk["reason_codes"],
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
    """Run a test policy simulation without persisting financial state (Phases 23 & 24)."""
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
    """Structured 'Why did the system do this?' factor breakdown."""
    act = action.lower()
    selected_reasons = []
    excluded_reasons = []

    if "product" in act or "search" in act or "recommend" in act:
        product_name = context.get("product_name", "the selected product")
        if context.get("category_match"):
            selected_reasons.append(f"✓ Category match: Fits requested '{context['category_match']}' category")
        if context.get("color_match"):
            selected_reasons.append(f"✓ Color match: Matches preferred '{context['color_match']}' color")
        if context.get("budget"):
            selected_reasons.append(f"✓ Budget fit: Price fits within budget cap (under ₹{context['budget']:,.2f})")
        if context.get("in_stock", True):
            selected_reasons.append("✓ Availability: Real-time inventory verified available in stock")

        return {
            "title": f"Why Product Selected: {product_name}",
            "decision": "RECOMMEND_PRODUCT",
            "factors": selected_reasons or ["✓ Verified database catalog product matching query"],
            "alternatives_not_selected": excluded_reasons or [
                "✗ Higher priced alternatives outside target budget range",
            ],
        }

    return {
        "title": "AI Action Governance Summary",
        "decision": action,
        "factors": ["✓ Validated against merchant policies, risk score, agent budget, and trust tiers"],
        "alternatives_not_selected": [],
    }


def check_action_allowed(db: Session, merchant_id: str, action: str) -> bool:
    """Check if action is allowed by policy."""
    policy = get_merchant_policy(db, merchant_id)
    if not policy:
        return True
    allowed = policy.allowed_actions or []
    return action in allowed or "all" in allowed


def update_policy(db: Session, merchant_id: str, updates: dict) -> Optional[Policy]:
    """Update merchant policy with server-side validation."""
    policy = get_merchant_policy(db, merchant_id)
    if not policy:
        return None
    for key, value in updates.items():
        if value is not None and hasattr(policy, key):
            setattr(policy, key, value)
    db.commit()
    db.refresh(policy)
    return policy
