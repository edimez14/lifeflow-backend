from __future__ import annotations

from sqlalchemy import text

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.database import AsyncSessionLocal
from app.websocket_manager import ConnectionManager

app = FastAPI(title="Lifeflow API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.get("/")
async def root() -> dict[str, str]:
    """Return a small response to confirm the API is running."""

    return {"message": "Lifeflow backend is running"}


@app.get("/health")
async def healthcheck() -> dict[str, str | bool]:
    """Check that the API and database are available."""

    db_ok = False
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar_one() == 1

    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
    }


@app.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str) -> None:
    """Handle the WebSocket connection for a workspace."""

    await manager.connect(workspace_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workspace_id, websocket)
