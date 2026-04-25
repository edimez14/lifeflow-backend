from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.models import Base
from app.main import app
from app.workspaces import models as workspace_models


def _create_all_tables(engine) -> None:
    """Create all tables in the in-memory database."""

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())


def _drop_all_tables(engine) -> None:
    """Drop all tables in the in-memory database."""

    async def _drop() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_drop())


@pytest.fixture()
def test_engine():
    """Create an in-memory SQLite engine shared across test connections."""

    _ = workspace_models
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _create_all_tables(engine)
    try:
        yield engine
    finally:
        _drop_all_tables(engine)
        asyncio.run(engine.dispose())


@pytest.fixture()
async def async_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for async tests."""

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session


@pytest.fixture()
def client(monkeypatch, test_engine) -> Generator[TestClient, None, None]:
    """Return a test client using the in-memory database engine."""

    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    monkeypatch.setattr("app.database.AsyncSessionLocal", session_factory)
    monkeypatch.setattr("app.core.router.AsyncSessionLocal", session_factory)

    with TestClient(app) as test_client:
        yield test_client
