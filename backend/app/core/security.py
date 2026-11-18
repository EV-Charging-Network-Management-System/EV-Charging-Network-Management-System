"""
Security & Cryptography Module.
Implements Argon2 password hashing via pwdlib and secure JWT access tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from backend.app.core.config import settings

# 1. Initialize Argon2 Password Hasher via pwdlib
_hasher = PasswordHash((Argon2Hasher(),))


def get_password_hash(password: str) -> str:
    """Hash plaintext password using Argon2."""
    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string.")
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify plaintext password against stored hash.
    Supports Argon2 hash verification and demo-fallback for pre-existing seed placeholders.
    """
    if not plain_password or not hashed_password:
        return False

    # Argon2 hash verification
    if hashed_password.startswith("$argon2"):
        try:
            return _hasher.verify(plain_password, hashed_password)
        except Exception:
            return False

    # Demo fallback for pre-seeded placeholder records (demo_placeholder_1..5)
    # Allows both exact placeholder string or friendly demo credentials in local environment
    if settings.ALLOW_DEMO_PASSWORDS and hashed_password.startswith("demo_placeholder_"):
        if plain_password == hashed_password:
            return True
        # Friendly aliases for testing seeded demo accounts
        if hashed_password == "demo_placeholder_4" and plain_password in ("admin123", "Admin@123", "demo_placeholder_4"):
            return True
        if hashed_password in ("demo_placeholder_1", "demo_placeholder_2", "demo_placeholder_5") and plain_password in ("demo123", "Customer@123"):
            return True
        if hashed_password == "demo_placeholder_3" and plain_password in ("operator123", "Operator@123"):
            return True

    return False


def validate_password_strength(password: str) -> bool:
    """
    Validates that password has at least 8 characters,
    including at least one letter and at least one digit.
    """
    if len(password) < 8:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit


def create_access_token(
    subject: int,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a secure cryptographically signed JWT access token.
    Claims include: sub (user_id), email, role, iat, exp.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "email": email,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError if invalid.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload

