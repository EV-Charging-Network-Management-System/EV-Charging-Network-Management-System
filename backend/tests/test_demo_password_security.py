"""Seed placeholders must not become valid credentials accidentally."""

from backend.app.core.config import settings
from backend.app.core.security import get_password_hash, verify_password


def test_seed_passwords_require_explicit_opt_in(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_PASSWORDS", False)
    assert not verify_password("admin123", "demo_placeholder_4")
    assert not verify_password("demo_placeholder_4", "demo_placeholder_4")

    monkeypatch.setattr(settings, "ALLOW_DEMO_PASSWORDS", True)
    assert verify_password("admin123", "demo_placeholder_4")
    assert not verify_password("wrong", "demo_placeholder_4")


def test_hashed_passwords_work_without_demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DEMO_PASSWORDS", False)
    password_hash = get_password_hash("secure-password-123")
    assert verify_password("secure-password-123", password_hash)
    assert not verify_password("wrong", password_hash)
