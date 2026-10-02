"""Global Kill Switch & System-Wide Operational Controls (Phase 4)."""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.services import audit_service

logger = logging.getLogger("agentpay.system_control")


class SystemControlService:
    """
    Manages system-wide emergency controls:
    - global_write_enabled: Blocks all financial and state mutations.
    - payments_enabled: Blocks checkout, payment creation, and refunds.
    - campaigns_enabled: Blocks AI campaign activation.
    - agent_execution_enabled: Blocks autonomous agent actions.
    """

    def __init__(self):
        self._global_write_enabled: bool = True
        self._payments_enabled: bool = True
        self._campaigns_enabled: bool = True
        self._agent_execution_enabled: bool = True
        self._last_state_change_reason: str = "System initialized in normal operational state"

    def get_status(self) -> Dict[str, Any]:
        """Return the current system operational status."""
        return {
            "global_write_enabled": self._global_write_enabled,
            "payments_enabled": self._payments_enabled,
            "campaigns_enabled": self._campaigns_enabled,
            "agent_execution_enabled": self._agent_execution_enabled,
            "status": "NORMAL" if (self._global_write_enabled and self._payments_enabled and self._agent_execution_enabled) else "PAUSED",
            "last_reason": self._last_state_change_reason,
        }

    def pause_all(self, db: Session, reason: str = "Emergency system freeze initiated", actor_id: str = "admin") -> Dict[str, Any]:
        """Emergency pause all system mutations and financial writes."""
        self._global_write_enabled = False
        self._payments_enabled = False
        self._campaigns_enabled = False
        self._agent_execution_enabled = False
        self._last_state_change_reason = reason

        audit_service.create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=actor_id,
            action="SYSTEM_PAUSE_ALL",
            resource_type="system",
            resource_id="global_kill_switch",
            reason=reason,
            result="SUCCESS",
            metadata_extra={"controls": self.get_status()},
        )
        logger.warning(f"🚨 GLOBAL KILL SWITCH ACTIVATED: {reason}")
        return self.get_status()

    def resume_all(self, db: Session, reason: str = "System resumed normal operations", actor_id: str = "admin") -> Dict[str, Any]:
        """Resume all normal operations."""
        self._global_write_enabled = True
        self._payments_enabled = True
        self._campaigns_enabled = True
        self._agent_execution_enabled = True
        self._last_state_change_reason = reason

        audit_service.create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=actor_id,
            action="SYSTEM_RESUME_ALL",
            resource_type="system",
            resource_id="global_kill_switch",
            reason=reason,
            result="SUCCESS",
            metadata_extra={"controls": self.get_status()},
        )
        logger.info(f"✅ SYSTEM RESUMED: {reason}")
        return self.get_status()

    def pause_payments(self, db: Session, reason: str = "Payment gateway paused for maintenance", actor_id: str = "admin") -> Dict[str, Any]:
        """Pause financial transactions while keeping catalog reads, analytics, and audit available."""
        self._payments_enabled = False
        self._last_state_change_reason = reason

        audit_service.create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=actor_id,
            action="SYSTEM_PAUSE_PAYMENTS",
            resource_type="system",
            resource_id="payments_switch",
            reason=reason,
            result="SUCCESS",
            metadata_extra={"controls": self.get_status()},
        )
        logger.warning(f"💳 PAYMENTS PAUSED: {reason}")
        return self.get_status()

    def pause_agents(self, db: Session, reason: str = "Autonomous agent execution paused", actor_id: str = "admin") -> Dict[str, Any]:
        """Pause autonomous agent operations while keeping human merchant controls active."""
        self._agent_execution_enabled = False
        self._last_state_change_reason = reason

        audit_service.create_audit_log(
            db=db,
            actor_type="admin",
            actor_id=actor_id,
            action="SYSTEM_PAUSE_AGENTS",
            resource_type="system",
            resource_id="agents_switch",
            reason=reason,
            result="SUCCESS",
            metadata_extra={"controls": self.get_status()},
        )
        logger.warning(f"🤖 AGENTS PAUSED: {reason}")
        return self.get_status()

    def check_writes_allowed(self) -> Dict[str, Any]:
        if not self._global_write_enabled:
            return {
                "allowed": False,
                "error_code": "SYSTEM_PAUSED",
                "message": f"Global system writes are paused: {self._last_state_change_reason}",
            }
        return {"allowed": True}

    def check_payments_allowed(self) -> Dict[str, Any]:
        if not self._global_write_enabled or not self._payments_enabled:
            return {
                "allowed": False,
                "error_code": "PAYMENTS_PAUSED",
                "message": f"Payment processing is currently paused by administrator: {self._last_state_change_reason}",
            }
        return {"allowed": True}

    def check_campaigns_allowed(self) -> Dict[str, Any]:
        if not self._global_write_enabled or not self._campaigns_enabled:
            return {
                "allowed": False,
                "error_code": "CAMPAIGNS_PAUSED",
                "message": f"Campaign activations are currently paused: {self._last_state_change_reason}",
            }
        return {"allowed": True}

    def check_agents_allowed(self) -> Dict[str, Any]:
        if not self._global_write_enabled or not self._agent_execution_enabled:
            return {
                "allowed": False,
                "error_code": "AGENTS_PAUSED",
                "message": f"Autonomous agent execution is currently paused: {self._last_state_change_reason}",
            }
        return {"allowed": True}


# Global singleton instance
system_control_service = SystemControlService()
