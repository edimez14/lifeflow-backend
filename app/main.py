from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.calendar.router import router as calendar_router
from app.core.router import router as core_router
from app.workspaces.router import router as workspaces_router
from app.tasks.router import router as tasks_router
from app.timer.router import router as timer_router
from app.websocket_manager import get_connection_manager


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Start and shut down the APScheduler on app lifecycle."""

    from app.scheduler import get_scheduler

    scheduler = get_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
app = FastAPI(title="Lifeflow API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router)
app.include_router(workspaces_router)
app.include_router(calendar_router)
app.include_router(tasks_router)
app.include_router(timer_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Return a small response to confirm the API is running."""

    return {"message": "Lifeflow backend is running"}


@app.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str) -> None:
    """Handle the WebSocket connection for a workspace."""

    manager = get_connection_manager()
    await manager.connect(workspace_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(workspace_id, websocket)
