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

    This function is the single entry point for all modules that need to
    send notifications. It reads the workspace's notification configuration,
    and sends via push (FCM) and/or email (SMTP) depending on the config.

    Currently (Módulo 4) the push and email backends are stubs.
    They will be fully implemented when Módulo 5 is developed.
    """

    import importlib
    try:
        config_module = importlib.import_module("app.notifications.models")
        config_model = getattr(config_module, "NotificationConfig", None)
    except (ImportError, ModuleNotFoundError):
        config_model = None

    if config_model is not None:
        from app.database import AsyncSessionLocal
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(config_model).where(
                    config_model.workspace_id == workspace_id,
                    config_model.event_type == notification_type,
                    config_model.active == True,
                )
            )
            configs = result.scalars().all()
    else:
        configs = []

    if not configs:
        await _send_fallback(workspace_id, notification_type, payload)
        return

    for cfg in configs:
        if cfg.channel in ("push", "both"):
            await _send_push(workspace_id, notification_type, payload, cfg)
        if cfg.channel in ("email", "both"):
            await _send_email(workspace_id, notification_type, payload, cfg)


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
