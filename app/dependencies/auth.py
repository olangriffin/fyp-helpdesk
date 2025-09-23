from typing import Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_session_token
from app.models import User
from app.models.enums import UserRole

settings = get_settings()

ROLE_REDIRECTS: Dict[UserRole, str] = {
    UserRole.requester: "/workspace",
    UserRole.it_manager: "/manager",
    UserRole.smartdesk_staff: "/admin/overview",
}


def role_redirect(role: str) -> str:
    try:
        role_enum = UserRole(role)
    except ValueError:
        return "/home"
    return ROLE_REDIRECTS.get(role_enum, "/home")


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_session_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive account")
    return user


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    payload = decode_session_token(token)
    if not payload:
        return None
    user = db.query(User).filter(User.id == payload.get("user_id")).first()
    if not user or not user.is_active:
        return None
    return user


def require_roles(*roles: UserRole):
    allowed = {role.value for role in roles}

    def dependency(user: User = Depends(get_current_user)) -> User:
        if allowed and user.primary_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency


def require_super_admin(user: User = Depends(get_current_user)) -> User:
    if user.email.lower() != settings.super_admin_email.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
