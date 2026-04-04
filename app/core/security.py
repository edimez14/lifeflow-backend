from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plain password for private workspaces."""

    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plain password against a stored hash."""

    return pwd_context.verify(plain_password, password_hash)


def create_workspace_token(workspace_id: str) -> str:
    """Create a short-lived JWT for a workspace session."""

    expire_at = datetime.now(
        UTC) + timedelta(hours=settings.access_token_expire_hours)
    payload = {
        "sub": workspace_id,
        "exp": expire_at,
        "iat": datetime.now(UTC),
        "type": "workspace",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_workspace_token(token: str) -> str:
    """Return the workspace id stored inside a valid JWT."""

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        workspace_id = payload.get("sub")
        token_type = payload.get("type")
    except JWTError as exc:
        raise ValueError("Invalid workspace token") from exc

    if token_type != "workspace" or not workspace_id:
        raise ValueError("Invalid workspace token")

    return str(workspace_id)


async def require_workspace_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Protect routes that require a valid workspace token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing workspace token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_workspace_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid workspace token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
