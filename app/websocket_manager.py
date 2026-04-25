from __future__ import annotations

from collections.abc import Iterable

from fastapi import WebSocket


class ConnectionManager:
    """Keep active WebSocket connections grouped by workspace."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, workspace_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""

        await websocket.accept()
        self.active_connections.setdefault(workspace_id, []).append(websocket)

    def disconnect(self, workspace_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from a workspace."""

        connections = self.active_connections.get(workspace_id)
        if not connections:
            return

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            self.active_connections.pop(workspace_id, None)

    async def broadcast(self, workspace_id: str, message: dict) -> None:
        """Send a JSON message to every client connected to a workspace."""

        connections = list(self.active_connections.get(workspace_id, []))
        if not connections:
            return

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(workspace_id, websocket)

    def connected_workspaces(self) -> Iterable[str]:
        """Return the workspace ids that currently have active clients."""

        return self.active_connections.keys()


# Global singleton instance
_connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """Dependency that returns the global connection manager."""

    return _connection_manager
