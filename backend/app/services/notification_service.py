"""Notification Center Service (Phase 33)."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

# In-memory and persisted notification queue
_notifications_store: List[Dict[str, Any]] = [
    {
        "id": "notif_001",
        "type": "APPROVAL_REQUIRED",
        "severity": "HIGH",
        "title": "Human Authorization Required",
        "message": "Autonomous order checkout of ₹4,999.00 gated for high transaction value.",
        "resource_type": "order",
        "resource_id": "ord_sample_001",
        "read": False,
        "created_at": str(datetime.now(timezone.utc)),
    },
    {
        "id": "notif_002",
        "type": "CIRCUIT_BREAKER_WARNING",
        "severity": "MEDIUM",
        "title": "Circuit Breaker Alert",
        "message": "ShoppingBot triggered 2 transient payment declines; failure counter monitored.",
        "resource_type": "agent",
        "resource_id": "ShoppingBot",
        "read": False,
        "created_at": str(datetime.now(timezone.utc)),
    },
    {
        "id": "notif_003",
        "type": "POLICY_CHECK_PASSED",
        "severity": "LOW",
        "title": "Policy Engine Baseline OK",
        "message": "Merchant limits validated against active inventory matrix.",
        "resource_type": "policy",
        "resource_id": "pol_merchant_001",
        "read": True,
        "created_at": str(datetime.now(timezone.utc)),
    },
]


def create_notification(
    event_type: str,
    title: str,
    message: str,
    severity: str = "INFO",  # LOW, MEDIUM, HIGH, CRITICAL
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enqueue a new governance or operational notification."""
    notif = {
        "id": f"notif_{uuid.uuid4().hex[:8]}",
        "type": event_type,
        "severity": severity.upper(),
        "title": title,
        "message": message,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "metadata": metadata or {},
        "read": False,
        "created_at": str(datetime.now(timezone.utc)),
    }
    _notifications_store.insert(0, notif)
    if len(_notifications_store) > 500:
        _notifications_store.pop()
    return notif


def list_notifications(severity: Optional[str] = None, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve notifications with optional severity filter."""
    res = _notifications_store
    if severity:
        res = [n for n in res if n.get("severity") == severity.upper()]
    if unread_only:
        res = [n for n in res if not n.get("read")]
    return res[:limit]


def mark_as_read(notification_id: str) -> bool:
    """Mark a single notification as read."""
    for n in _notifications_store:
        if n["id"] == notification_id:
            n["read"] = True
            return True
    return False


def mark_all_as_read() -> int:
    """Mark all notifications as read."""
    count = 0
    for n in _notifications_store:
        if not n["read"]:
            n["read"] = True
            count += 1
    return count
