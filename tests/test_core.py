from __future__ import annotations

from app.config import settings
from app.core.security import (
    create_workspace_token,
    decode_workspace_token,
    hash_password,
    verify_password,
)


def test_healthcheck_returns_ok(client) -> None:
    """The healthcheck should confirm API and database availability."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "database": True,
    }


def test_hash_and_verify_password() -> None:
    """Password hashing must be reversible only through verification."""

    password_hash = hash_password("secret-password")

    assert password_hash != "secret-password"
    assert verify_password("secret-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_workspace_token_roundtrip(monkeypatch) -> None:
    """Workspace tokens should encode and decode the workspace id."""

    monkeypatch.setattr(settings, "secret_key", "test-secret-key")
    monkeypatch.setattr(settings, "access_token_expire_hours", 1)

    token = create_workspace_token("workspace-123")

    assert isinstance(token, str)
    assert decode_workspace_token(token) == "workspace-123"
