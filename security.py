"""Security utilities: password hashing and JWT token management."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Check if we are in a production environment (Railway sets this, or we can set it)
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

# In production, strictly require the environment variable. In dev, allow the fallback.
if IS_PRODUCTION:
    SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("CRITICAL: JWT_SECRET_KEY environment variable is not set in production!")
else:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "local-dev-secret-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: dict | None = None) -> str:
    """Create a signed JWT with an expiration claim.

    *subject* is stored in the ``sub`` claim (typically the user id).
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload: dict = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises ``jwt.PyJWTError`` on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
