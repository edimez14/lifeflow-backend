from __future__ import annotations

import logging

from app.websocket_manager import get_connection_manager

logger = logging.getLogger("lifeflow.notifications")


async def dispatch_notification(
    workspace_id: str,
    notification_type: str,
    payload: dict,
) -> None:
    """Dispatch a notification to the workspace.

    Currently all notifications are sent via WebSocket (fallback).
    Push (FCM) and email (SMTP) backends are stubs — they will be
    wired once NotificationConfig model is implemented (Módulo 5).
    """

    await _send_fallback(workspace_id, notification_type, payload)


async def _send_fallback(
    workspace_id: str,
    notification_type: str,
    payload: dict,
) -> None:
    """Fallback: broadcast notification via WebSocket when no config exists."""

    manager = get_connection_manager()
    await manager.broadcast(
        workspace_id,
        {
            "type": f"notification.{notification_type}",
            "data": {
                "workspace_id": workspace_id,
                "notification_type": notification_type,
                "payload": payload,
            },
        },
    )


async def _send_push(
    workspace_id: str,
    notification_type: str,
    payload: dict,
    config: object,
) -> None:
    """Send a push notification via FCM. Stub until Módulo 5."""

    logger.info(
        "[PUSH STUB] workspace=%s type=%s payload=%s",
        workspace_id, notification_type, payload,
    )


async def _send_email(
    workspace_id: str,
    notification_type: str,
    payload: dict,
    config: object,
) -> None:
    """Send an email notification via SMTP. Stub until Módulo 5."""

    logger.info(
        "[EMAIL STUB] workspace=%s type=%s payload=%s",
        workspace_id, notification_type, payload,
    )
