from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings


if not hasattr(bcrypt, "__about__"):
    class _BcryptAbout:
        """Compatibility shim for passlib with modern bcrypt versions."""

        __version__ = getattr(bcrypt, "__version__", "")

    bcrypt.__about__ = _BcryptAbout()  # type: ignore[attr-defined]


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def _hash_with_bcrypt_backend(password: str) -> str:
    """Hash password using bcrypt library directly."""

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_with_bcrypt_backend(plain_password: str, password_hash: str) -> bool:
    """Verify password using bcrypt library directly."""

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        return False


def hash_password(password: str) -> str:
    """Hash a plain password for private workspaces."""

    try:
        return pwd_context.hash(password)
    except Exception:
        return _hash_with_bcrypt_backend(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plain password against a stored hash."""

    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return _verify_with_bcrypt_backend(plain_password, password_hash)


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
