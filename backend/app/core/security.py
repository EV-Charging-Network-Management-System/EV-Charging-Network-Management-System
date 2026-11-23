"""
Security & Cryptography Module.
Implements Argon2 password hashing via pwdlib and secure JWT access tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

import jwt
from argon2.exceptions import VerificationError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
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
    """Verify an Argon2 password hash."""
    if not plain_password or not hashed_password.startswith("$argon2"):
        return False
    try:
        return _hasher.verify(plain_password, hashed_password)
    except (ValueError, TypeError, VerificationError, UnknownHashError):
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
        "jti": uuid4().hex,
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
        algorithms=[settings.ALGORITHM],
        options={"require": ["exp", "iat", "sub", "jti", "type"]},
    )
    if payload["type"] != "access":
        raise jwt.InvalidTokenError("Expected an access token")
    return payload

