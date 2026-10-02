"""Circuit Breaker Service — State machine for agent/payment execution safety (Phase 6)."""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.services import audit_service

logger = logging.getLogger("agentpay.circuit_breaker")


class CircuitBreakerService:
    """
    State Machine:
    - CLOSED: Normal operation. Financial transactions proceed.
    - OPEN: Tripped due to repeated failures. Financial actions blocked.
    - HALF_OPEN: Cooldown elapsed. Allows a single probe transaction to test recovery.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: int = 60,
        half_open_test_limit: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.half_open_test_limit = half_open_test_limit

    def get_state(self, db: Session, agent_id: str) -> Dict[str, Any]:
        """Query authoritative circuit breaker state with automatic cooldown transition."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"state": "CLOSED", "tripped": False, "reason": None}

        current_state = agent.circuit_breaker_state or "CLOSED"
        now = datetime.now(timezone.utc)

        # Check if OPEN has cooled down into HALF_OPEN
        if current_state == "OPEN" and agent.circuit_breaker_opened_at:
            opened_at = agent.circuit_breaker_opened_at
            if opened_at.tzinfo is None:
                opened_at = opened_at.replace(tzinfo=timezone.utc)
            elapsed = (now - opened_at).total_seconds()
            if elapsed >= self.cooldown_seconds:
                agent.circuit_breaker_state = "HALF_OPEN"
                agent.circuit_breaker_reason = f"Cooldown ({self.cooldown_seconds}s) elapsed. Probing with limited test throughput."
                db.commit()
                db.refresh(agent)

                audit_service.create_audit_log(
                    db=db,
                    actor_type="system",
                    actor_id="circuit_breaker",
                    action="CIRCUIT_HALF_OPEN",
                    resource_type="agent",
                    resource_id=agent_id,
                    reason=agent.circuit_breaker_reason,
                    result="SUCCESS",
                    metadata_extra={"state": "HALF_OPEN", "agent_id": agent_id},
                )
                current_state = "HALF_OPEN"

        return {
            "state": current_state,
            "tripped": current_state in ("OPEN", "HALF_OPEN"),
            "failed_payment_count": agent.failed_payment_count or 0,
            "failure_threshold": self.failure_threshold,
            "cooldown_seconds": self.cooldown_seconds,
            "reason": agent.circuit_breaker_reason,
            "opened_at": str(agent.circuit_breaker_opened_at) if agent.circuit_breaker_opened_at else None,
        }

    def can_execute(self, db: Session, agent_id: str) -> Dict[str, Any]:
        """Check if financial actions are permitted through the circuit breaker."""
        status = self.get_state(db, agent_id)
        state = status["state"]

        if state == "OPEN":
            return {
                "allowed": False,
                "error_code": "CIRCUIT_OPEN",
                "message": f"Circuit breaker is OPEN for agent '{agent_id}': {status.get('reason')}",
                "circuit_state": status,
            }

        return {
            "allowed": True,
            "circuit_state": status,
            "is_probe": state == "HALF_OPEN",
        }

    def record_failure(
        self,
        db: Session,
        agent_id: str,
        reason: str = "Payment transaction failed",
    ) -> Dict[str, Any]:
        """Record an execution failure and trip circuit if threshold exceeded."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            agent = Agent(
                id=agent_id,
                name=agent_id,
                role="shopping",
                owner="system",
                status="ACTIVE",
                permissions=["all"],
                daily_budget=10000.0,
                per_transaction_limit=5000.0,
            )
            db.add(agent)
            db.commit()
            db.refresh(agent)

        now = datetime.now(timezone.utc)
        current_state = agent.circuit_breaker_state or "CLOSED"

        # If already HALF_OPEN and fails again -> immediately back to OPEN with reset timer
        if current_state == "HALF_OPEN":
            agent.circuit_breaker_state = "OPEN"
            agent.circuit_breaker_tripped = True
            agent.circuit_breaker_opened_at = now
            agent.circuit_breaker_reason = f"Probe transaction failed: {reason}"
            db.commit()

            audit_service.create_audit_log(
                db=db,
                actor_type="system",
                actor_id="circuit_breaker",
                action="CIRCUIT_OPENED",
                resource_type="agent",
                resource_id=agent_id,
                reason=agent.circuit_breaker_reason,
                result="FAILURE",
                metadata_extra={"state": "OPEN", "trigger": "HALF_OPEN_PROBE_FAILED"},
            )
            return self.get_state(db, agent_id)

        # In CLOSED state, accumulate failures
        agent.failed_payment_count = (agent.failed_payment_count or 0) + 1
        agent.last_failure_time = now

        if agent.failed_payment_count >= self.failure_threshold:
            agent.circuit_breaker_state = "OPEN"
            agent.circuit_breaker_tripped = True
            agent.circuit_breaker_opened_at = now
            agent.circuit_breaker_reason = f"Consecutive failure threshold reached ({agent.failed_payment_count}/{self.failure_threshold}): {reason}"

            audit_service.create_audit_log(
                db=db,
                actor_type="system",
                actor_id="circuit_breaker",
                action="CIRCUIT_OPENED",
                resource_type="agent",
                resource_id=agent_id,
                reason=agent.circuit_breaker_reason,
                result="FAILURE",
                metadata_extra={"state": "OPEN", "failed_count": agent.failed_payment_count},
            )
            logger.error(f"🔴 CIRCUIT BREAKER TRIPPED to OPEN for agent {agent_id}: {agent.circuit_breaker_reason}")

        db.commit()
        db.refresh(agent)
        return self.get_state(db, agent_id)

    def record_success(self, db: Session, agent_id: str) -> Dict[str, Any]:
        """Record successful execution. If in HALF_OPEN, closes circuit breaker."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"state": "CLOSED"}

        current_state = agent.circuit_breaker_state or "CLOSED"

        if current_state == "HALF_OPEN" or agent.circuit_breaker_tripped:
            agent.circuit_breaker_state = "CLOSED"
            agent.circuit_breaker_tripped = False
            agent.failed_payment_count = 0
            agent.circuit_breaker_reason = "Probe successful. Circuit returned to normal CLOSED state."
            agent.circuit_breaker_opened_at = None
            db.commit()

            audit_service.create_audit_log(
                db=db,
                actor_type="system",
                actor_id="circuit_breaker",
                action="CIRCUIT_CLOSED",
                resource_type="agent",
                resource_id=agent_id,
                reason=agent.circuit_breaker_reason,
                result="SUCCESS",
                metadata_extra={"state": "CLOSED"},
            )
            logger.info(f"🟢 CIRCUIT BREAKER CLOSED for agent {agent_id}")
        else:
            # Gradually decay failure counter on success
            if agent.failed_payment_count and agent.failed_payment_count > 0:
                agent.failed_payment_count = max(0, agent.failed_payment_count - 1)
                db.commit()

        db.refresh(agent)
        return self.get_state(db, agent_id)

    def reset_circuit(self, db: Session, agent_id: str, reason: str = "Manual admin override", actor_id: str = "admin") -> Dict[str, Any]:
        """Alias for manual_reset."""
        res = self.manual_reset(db, agent_id, actor_id=actor_id)
        res["success"] = True
        return res

    def manual_reset(self, db: Session, agent_id: str, actor_id: str = "admin") -> Dict[str, Any]:
        """Admin manual reset of the circuit breaker."""
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return {"error": True, "message": "Agent not found"}

        agent.circuit_breaker_state = "CLOSED"
        agent.circuit_breaker_tripped = False
        agent.failed_payment_count = 0
        agent.circuit_breaker_reason = "Manually reset by administrator"
        agent.circuit_breaker_opened_at = None
        db.commit()

        audit_service.create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=actor_id,
            action="CIRCUIT_CLOSED",
            resource_type="agent",
            resource_id=agent_id,
            reason=agent.circuit_breaker_reason,
            result="SUCCESS",
            metadata_extra={"state": "CLOSED", "manual_reset": True},
        )
        return self.get_state(db, agent_id)


# Global singleton instance
circuit_breaker_service = CircuitBreakerService()
