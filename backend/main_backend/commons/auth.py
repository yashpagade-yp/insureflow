"""Authentication utilities for JWT, password, and OTP management."""

from __future__ import annotations

import hashlib
import os
import secrets
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv
from passlib.context import CryptContext


ENV_FILE_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_FILE_PATH)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
OTP_SECRET = os.environ.get("OTP_SECRET_KEY") or os.environ.get(
    "JWT_SECRET_KEY",
    "insureflow-main-otp-secret",
)

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET_KEY is required in main_backend/.env")


def signJWT(user_role: str, id: str, expiry_duration: int | None = None) -> str:
    """
    Create a signed JWT access token for the given user.

    The token payload contains:
        - user_role: role of the user (e.g., "USER", "ADMIN")
        - id: user's unique identifier (ObjectId as string)
        - expires: Unix timestamp when this token expires

    Args:
        user_role: Role string from UserRole enum
        id: User ID as string
        expiry_duration: Seconds until expiry. If omitted, uses
            JWT_EXPIRY_HOURS from environment.

    Returns:
        str: Signed JWT token string
    """
    expiry_seconds = expiry_duration or (JWT_EXPIRY_HOURS * 3600)
    payload = {
        "user_role": user_role,
        "id": id,
        "expires": time.time() + expiry_seconds,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decodeJWT(token: str) -> dict | None:
    """
    Decode and validate a JWT token.

    Returns the decoded payload if valid and not expired.
    Returns None if the token is invalid or expired.

    Args:
        token: JWT string to decode

    Returns:
        dict | None: Decoded payload or None
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded if decoded.get("expires", 0) > time.time() else None
    except Exception:
        return None


def encrypt_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""

    return pwd_context.verify(plain_password, hashed_password)


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP with the requested number of digits."""

    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(otp: str) -> str:
    """Hash an OTP before persisting it to storage."""

    payload = f"{otp}:{OTP_SECRET}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_hashed_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Compare a plain OTP against its hashed representation."""

    return secrets.compare_digest(hash_otp(plain_otp), hashed_otp)
