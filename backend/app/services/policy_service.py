"""Policy service — evaluates financial action policies."""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.policy import Policy


def get_merchant_policy(db: Session, merchant_id: str) -> Optional[Policy]:
    """Get the policy for a merchant."""
    return db.query(Policy).filter(Policy.merchant_id == merchant_id).first()


def check_purchase_policy(db: Session, merchant_id: str, amount: float) -> dict:
    """
    Evaluate purchase against merchant policy.
    Returns structured allow/deny result.
    """
    policy = get_merchant_policy(db, merchant_id)

    if not policy:
        # No policy — allow with approval
        return {
            "allowed": True,
            "reason": "No policy configured — default allow",
            "requires_approval": True,
            "details": {"amount": amount},
        }

    # Check amount limit
    if amount > policy.max_purchase_amount:
        return {
            "allowed": False,
            "reason": f"Amount ₹{amount} exceeds configured purchase limit of ₹{policy.max_purchase_amount}",
            "requires_approval": False,
            "details": {
                "requested_amount": amount,
                "maximum_allowed": policy.max_purchase_amount,
            },
        }

    return {
        "allowed": True,
        "reason": f"Amount ₹{amount} is within the allowed limit of ₹{policy.max_purchase_amount}",
        "requires_approval": policy.approval_required,
        "details": {
            "requested_amount": amount,
            "maximum_allowed": policy.max_purchase_amount,
            "approval_required": policy.approval_required,
        },
    }


def check_action_allowed(db: Session, merchant_id: str, action: str) -> bool:
    """Check if a specific action is allowed by policy."""
    policy = get_merchant_policy(db, merchant_id)
    if not policy:
        return True
    return action in (policy.allowed_actions or [])


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
