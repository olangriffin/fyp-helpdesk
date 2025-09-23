import json
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_session_token,
    generate_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.core.session import clear_session_cookie, set_session_cookie
from app.dependencies.auth import get_current_user, role_redirect
from app.models import User
from app.models.enums import UserRole
from app.schemas.user import (
    EmailVerificationRequest,
    ResendVerificationRequest,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.notifications import send_verification_email
from app.services.organizations import (
    add_or_update_membership,
    create_organization,
    get_organization_by_slug,
)

router = APIRouter(tags=["auth"])


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "org"


def _ensure_unique_slug(db: Session, slug: str) -> str:
    candidate = slug
    suffix = 1
    while get_organization_by_slug(db, candidate):
        suffix += 1
        candidate = f"{slug}-{suffix}"
    return candidate


def _coerce_role(value: UserRole | str) -> str:
    return value.value if isinstance(value, UserRole) else value


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    try:
        validate_password_strength(payload.password)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    password_data = hash_password(payload.password)
    primary_role = _coerce_role(payload.primary_role)
    verification_token = generate_token()
    now = datetime.now(timezone.utc)

    user = User(
        email=email,
        password_hash=password_data["hash"],
        password_salt=password_data["salt"],
        full_name=payload.full_name,
        job_title=payload.job_title,
        department=payload.department,
        primary_role=primary_role,
        permissions=json.dumps({}),
        role_overrides=json.dumps({}),
        profile_complete=bool(payload.full_name),
        verification_token=verification_token,
        verification_sent_at=now,
        password_updated_at=now,
        email_verified=False,
        last_login_at=None,
        last_login_ip=request.client.host if request.client else None,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    if payload.organization_name:
        slug = payload.organization_slug or _slugify(payload.organization_name)
        slug = _ensure_unique_slug(db, slug)
        organization = create_organization(
            db,
            name=payload.organization_name,
            slug=slug,
            description=f"Created by {user.full_name or user.email}",
            contact_email=email,
        )
        add_or_update_membership(
            db,
            user_id=user.id,
            organization_id=organization.id,
            role=primary_role,
            is_owner=True,
        )

    send_verification_email(email=email, token=verification_token)

    return JSONResponse(
        {
            "redirect_url": "/auth?mode=login",
            "requires_verification": True,
            "message": "Account created. Please verify your email before logging in.",
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login")
def login(
    payload: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash, user.password_salt):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    user.last_login_at = datetime.now(timezone.utc)
    if request.client:
        user.last_login_ip = request.client.host
    db.commit()
    db.refresh(user)

    token = create_session_token(user)
    redirect_url = role_redirect(user.primary_role)
    response = JSONResponse({"redirect_url": redirect_url, "user": UserRead.from_orm(user).dict()})
    set_session_cookie(response, token)
    return response


@router.post("/verify-email")
def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == payload.token).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.email_verified = True
    user.verification_token = None
    user.verification_sent_at = None
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "Email verified. You can now log in."}


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user: Optional[User] = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")

    token = generate_token()
    user.verification_token = token
    user.verification_sent_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    send_verification_email(email=email, token=token)
    return {"success": True, "message": "Verification email sent."}


@router.get("/google/start")
def google_oauth_start():
    return JSONResponse(
        {
            "detail": "Google OAuth is not configured in this environment. Provide client credentials to enable.",
        },
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )


@router.get("/google/callback")
def google_oauth_callback():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google OAuth not configured")


@router.post("/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"success": True}


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
