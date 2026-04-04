from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app.database import AsyncSessionLocal


router = APIRouter(tags=["core"])


@router.get("/health")
async def healthcheck() -> dict[str, str | bool]:
    """Check that the API and database are available."""

    db_ok = False
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        db_ok = result.scalar_one() == 1

    return {
        "status": "ok" if db_ok else "degraded",
        "version": "0.1.0",
        "database": db_ok,
    }
