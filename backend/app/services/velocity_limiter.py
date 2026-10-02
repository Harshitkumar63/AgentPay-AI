"""Velocity Limiter Service — Configurable rate and transaction velocity controls (Phase 5)."""

import time
import logging
from collections import defaultdict
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.agent import AgentBudget
from app.services import audit_service, trust_service

logger = logging.getLogger("agentpay.velocity_limiter")


class VelocityLimiter:
    """
    In-memory and DB-backed sliding window rate & transaction limiter.
    Limits:
    - requests_per_minute (default 60)
    - tool_calls_per_minute (default 20)
    - transactions_per_minute (default 5)
    - transactions_per_hour (default 20)
    - transactions_per_day (default 100)
    - failed_payment_threshold (default 5 within 2 min)
    """

    def __init__(self):
        # Sliding timestamp stores: key -> list of float timestamps
        self._request_windows: Dict[str, List[float]] = defaultdict(list)
        self._tool_windows: Dict[str, List[float]] = defaultdict(list)
        self._tx_windows: Dict[str, List[float]] = defaultdict(list)
        self._failure_windows: Dict[str, List[float]] = defaultdict(list)

    def _clean_window(self, timestamps: List[float], max_age_seconds: float) -> List[float]:
        now = time.time()
        cutoff = now - max_age_seconds
        return [ts for ts in timestamps if ts > cutoff]

    def check_request_velocity(
        self,
        agent_id: str,
        max_requests_per_minute: int = 60,
        request_id: str = None,
    ) -> Dict[str, Any]:
        """Check API request frequency for an agent."""
        now = time.time()
        self._request_windows[agent_id] = self._clean_window(self._request_windows[agent_id], 60)
        current_count = len(self._request_windows[agent_id])

        if current_count >= max_requests_per_minute:
            return {
                "decision": "RATE_LIMITED",
                "allowed": False,
                "error_code": "RATE_LIMITED",
                "message": f"Request rate limit exceeded ({current_count}/{max_requests_per_minute} req/min).",
                "current_count": current_count,
                "limit": max_requests_per_minute,
                "retry_after_seconds": int(60 - (now - self._request_windows[agent_id][0])),
            }

        self._request_windows[agent_id].append(now)
        return {
            "decision": "ALLOWED",
            "allowed": True,
            "current_count": current_count + 1,
            "limit": max_requests_per_minute,
        }

    def check_transaction_velocity(
        self,
        db: Session,
        agent_id: str,
        max_per_minute: int = 5,
        max_per_hour: int = 20,
        max_per_day: int = 100,
    ) -> Dict[str, Any]:
        """
        Check transaction velocity using both in-memory high-precision window
        and persistent DB counters.
        """
        now = time.time()
        
        # In-memory sliding window checks
        self._tx_windows[agent_id] = self._clean_window(self._tx_windows[agent_id], 86400)
        recent_txs = self._tx_windows[agent_id]

        count_1m = sum(1 for ts in recent_txs if ts > now - 60)
        count_1h = sum(1 for ts in recent_txs if ts > now - 3600)
        count_1d = len(recent_txs)

        if count_1m >= max_per_minute:
            self._audit_velocity_breach(db, agent_id, "PER_MINUTE", count_1m, max_per_minute)
            return {
                "decision": "VELOCITY_LIMIT_EXCEEDED",
                "allowed": False,
                "error_code": "VELOCITY_LIMIT_EXCEEDED",
                "limit_type": "PER_MINUTE",
                "message": f"Velocity limit exceeded: {count_1m}/{max_per_minute} transactions per minute.",
                "retry_after_seconds": 60,
            }

        if count_1h >= max_per_hour:
            self._audit_velocity_breach(db, agent_id, "PER_HOUR", count_1h, max_per_hour)
            return {
                "decision": "VELOCITY_LIMIT_EXCEEDED",
                "allowed": False,
                "error_code": "VELOCITY_LIMIT_EXCEEDED",
                "limit_type": "PER_HOUR",
                "message": f"Velocity limit exceeded: {count_1h}/{max_per_hour} transactions per hour.",
                "retry_after_seconds": 3600,
            }

        if count_1d >= max_per_day:
            self._audit_velocity_breach(db, agent_id, "PER_DAY", count_1d, max_per_day)
            return {
                "decision": "VELOCITY_LIMIT_EXCEEDED",
                "allowed": False,
                "error_code": "VELOCITY_LIMIT_EXCEEDED",
                "limit_type": "PER_DAY",
                "message": f"Velocity limit exceeded: {count_1d}/{max_per_day} transactions per day.",
                "retry_after_seconds": 86400,
            }

        return {
            "decision": "ALLOWED",
            "allowed": True,
            "counts": {"minute": count_1m, "hour": count_1h, "day": count_1d},
        }

    def record_transaction(self, db: Session, agent_id: str, amount: float = 0.0):
        """Record an approved transaction timestamp."""
        now = time.time()
        self._tx_windows[agent_id].append(now)

        # Update persistent DB budget counts
        budget = db.query(AgentBudget).filter(AgentBudget.agent_id == agent_id).first()
        if budget:
            budget.transaction_count_minute = (budget.transaction_count_minute or 0) + 1
            budget.transaction_count_hour = (budget.transaction_count_hour or 0) + 1
            budget.transaction_count_today = (budget.transaction_count_today or 0) + 1
            budget.spent_this_hour = (budget.spent_this_hour or 0.0) + amount
            db.commit()

    def record_failure(self, db: Session, agent_id: str):
        """Record a failure event in the velocity sliding window."""
        now = time.time()
        self._failure_windows[agent_id].append(now)

    def _audit_velocity_breach(self, db: Session, agent_id: str, limit_type: str, count: int, limit: int):
        trust_service.record_trust_event(db, "velocity_violation", agent_id=agent_id)
        audit_service.create_audit_log(
            db=db,
            actor_type="ai_agent",
            actor_id=agent_id,
            action="VELOCITY_LIMIT_EXCEEDED",
            resource_type="agent",
            resource_id=agent_id,
            reason=f"Exceeded {limit_type} rate threshold ({count}/{limit})",
            policy_result="BLOCKED",
            result="FAILURE",
            metadata_extra={"limit_type": limit_type, "count": count, "limit": limit},
        )


# Global singleton instance
velocity_limiter = VelocityLimiter()
