"""
User Management Endpoints.
Implements customer self-service profile access and admin-only management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, require_admin
from backend.app.models.user import User
from backend.app.models.workflow import AdminAuditEvent
from backend.app.schemas.user import UserResponse, UserUpdateProfile, UserStatusUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
def read_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """Returns the authenticated user's own profile."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile"
)
def update_current_user_profile(
    profile_in: UserUpdateProfile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Allows authenticated users to update their name and phone number.
    Security: Role and email modifications by standard users are strictly forbidden.
    """
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name.strip()
    if profile_in.phone is not None:
        current_user.phone = profile_in.phone.strip()

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List all users (Admin only)"
)
def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[str] = Query(None, pattern="^(CUSTOMER|OPERATOR|ADMIN)$"),
    is_active: Optional[bool] = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """
    Administrative endpoint to retrieve user list with optional role/status filters.
    Requires ADMIN privileges.
    """
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.order_by(User.user_id).offset(skip).limit(limit).all()
    return users


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Activate or Deactivate User Account (Admin only)"
)
def update_user_status(
    user_id: int,
    status_in: UserStatusUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Administrative endpoint to activate or deactivate a user account.
    Prevents self-deactivation by the acting admin.
    """
    user = db.query(User).filter(User.user_id == user_id).with_for_update(of=User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} was not found."
        )

    # Prevent accidental self-deactivation
    if user.user_id == current_admin.user_id and not status_in.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own active account."
        )

    db.add(AdminAuditEvent(
        actor_id=current_admin.user_id, action="user.status_changed", resource_id=user_id, details={"before": user.is_active, "after": status_in.is_active},
    ))
    user.is_active = status_in.is_active
    db.add(user)
    db.commit()
    db.refresh(user)

    return user
