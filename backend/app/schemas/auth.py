"""
Authentication Schemas (Pydantic v2).
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.user import UserResponse

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserRegister(BaseModel):
    """
    Public registration schema.
    Defaults to CUSTOMER role. Does not accept role inputs from public clients.
    """
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., pattern=EMAIL_PATTERN, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Credentials required for login."""
    email: str = Field(..., pattern=EMAIL_PATTERN, max_length=150)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """JWT Token and safe user response payload."""
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out."
