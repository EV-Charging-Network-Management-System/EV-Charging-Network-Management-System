"""
Authentication Endpoints: Register, Login, Me, Logout.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_strength,
    create_access_token,
    decode_access_token
)
from backend.app.api.deps import ACCESS_COOKIE, BROWSER_HEADER, get_access_token, get_current_active_user
from backend.app.models.revoked_token import RevokedToken
from backend.app.models.user import User
from backend.app.schemas.auth import UserRegister, UserLogin, TokenResponse, LogoutResponse
from backend.app.schemas.user import UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account"
)
def register(user_in: UserRegister, db: Session = Depends(get_db)) -> UserResponse:
    """
    Public registration endpoint.
    - Strictly defaults role to CUSTOMER (public registration as ADMIN/OPERATOR is prohibited).
    - Validates email uniqueness.
    - Validates password strength.
    - Hashes password using Argon2 via pwdlib.
    - Returns safe user details (never returns password_hash).
    """
    # 1. Normalize and check email uniqueness
    normalized_email = user_in.email.strip().lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # 2. Validate password strength
    if not validate_password_strength(user_in.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long and contain both letters and numbers."
        )

    # 3. Hash password using Argon2
    hashed_password = get_password_hash(user_in.password)

    # 4. Create and persist user entity
    new_user = User(
        full_name=user_in.full_name.strip(),
        email=normalized_email,
        phone=user_in.phone.strip() if user_in.phone else None,
        password_hash=hashed_password,
        role="CUSTOMER",  # Enforcement: public registrations are ALWAYS CUSTOMER
        is_active=True
    )

    db.add(new_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) != "23505":
            raise
        raise HTTPException(status_code=400, detail="A user with this email address already exists.") from exc
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login & JWT Token Generation"
)
def login(credentials: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticates a user via email and password.
    - Rejects invalid credentials.
    - Rejects deactivated accounts.
    - Issues a cryptographically signed JWT access token.
    - Returns safe user profile (without password hash).
    """
    normalized_email = credentials.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support or an administrator."
        )

    access_token = create_access_token(
        subject=user.user_id,
        email=user.email,
        role=user.role
    )

    response.headers["Cache-Control"] = "no-store"
    if request.headers.get(BROWSER_HEADER) == "1":
        response.set_cookie(
            ACCESS_COOKIE, access_token, httponly=True, secure=settings.SECURE_COOKIES,
            samesite="lax", max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path=settings.API_V1_STR,
        )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user profile"
)
def get_me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    """Returns the profile of the currently authenticated user."""
    return current_user


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User Logout"
)
def logout(
    response: Response,
    token: str = Depends(get_access_token),
    _current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LogoutResponse:
    """Revoke this token until its expiration and clear the browser cookie."""
    claims = decode_access_token(token)
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at <= datetime.now(timezone.utc)))
    db.execute(
        insert(RevokedToken)
        .values(token_id=claims["jti"], expires_at=datetime.fromtimestamp(claims["exp"], timezone.utc))
        .on_conflict_do_nothing()
    )
    db.commit()
    response.delete_cookie(ACCESS_COOKIE, path=settings.API_V1_STR)
    return LogoutResponse()
