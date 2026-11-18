"""
Pydantic v2 validation schemas for Users.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserBase(BaseModel):
    full_name: str = Field(..., max_length=100)
    email: str = Field(..., pattern=EMAIL_PATTERN, max_length=150)
    phone: Optional[str] = Field(None, max_length=20)
    role: str = Field("CUSTOMER", pattern="^(CUSTOMER|OPERATOR|ADMIN)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdateProfile(BaseModel):
    """Fields that regular users are allowed to update on their own profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class UserStatusUpdate(BaseModel):
    """Admin-only update to activate/deactivate account."""
    is_active: bool


class UserResponse(UserBase):
    """Safe user profile response; NEVER contains password or password_hash."""
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    is_active: bool
    created_at: datetime
