"""Seed placeholders remain unusable and Argon2 hashes authenticate normally."""

from backend.app.core.security import get_password_hash, verify_password


def test_seed_passwords_are_rejected():
    assert not verify_password("admin123", "demo_placeholder_4")
    assert not verify_password("demo_placeholder_4", "demo_placeholder_4")
    assert not verify_password("malformed", "$argon2invalid")


def test_hashed_passwords_work():
    password_hash = get_password_hash("secure-password-123")
    assert verify_password("secure-password-123", password_hash)
    assert not verify_password("wrong", password_hash)
