"""Notifications API Endpoints (Phase 33)."""

from typing import Optional, List
from fastapi import APIRouter, Query
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notification Center"])


@router.get("", summary="List Notifications")
def get_notifications(
    severity: Optional[str] = Query(default=None, example="HIGH"),
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, le=100),
):
    """Retrieve system, governance, risk, and approval alerts."""
    return notification_service.list_notifications(severity=severity, unread_only=unread_only, limit=limit)


@router.post("/{notification_id}/read", summary="Mark Notification Read")
def mark_read(notification_id: str):
    """Mark a notification as read."""
    success = notification_service.mark_as_read(notification_id)
    return {"success": success, "notification_id": notification_id}


@router.post("/read-all", summary="Mark All Notifications Read")
def mark_all_read():
    """Mark all active notifications as read."""
    count = notification_service.mark_all_as_read()
    return {"success": True, "marked_count": count}
