from __future__ import annotations

from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app


@pytest.fixture()
def test_engine():
    """Create an in-memory SQLite engine shared across test connections."""

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        yield engine
    finally:
        pass


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
    monkeypatch.setattr("app.main.AsyncSessionLocal", session_factory)

    with TestClient(app) as test_client:
        yield test_client
