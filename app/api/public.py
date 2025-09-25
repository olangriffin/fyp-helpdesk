from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.templates import templates
from app.core.database import get_db
from app.dependencies.auth import (
    get_current_user,
    get_optional_user,
    require_roles,
    require_super_admin,
    role_redirect,
)
from app.models import Organization, User
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.services.tickets import ISSUE_TYPES
from app.services import tickets as ticket_service
from app.services.metrics import platform_overview
from app.services.organizations import get_primary_membership
from app.models.membership import Membership

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
def home(request: Request, current_user: Optional[User] = Depends(get_optional_user)):
    if current_user:
        return RedirectResponse(role_redirect(current_user.primary_role), status_code=status.HTTP_302_FOUND)

    roles = [
        {
            "value": role.value,
            "label": "SmartDesk Staff" if role == UserRole.smartdesk_staff else ("IT Manager" if role == UserRole.it_manager else "Requester"),
        }
        for role in UserRole
    ]

    context = {
        "request": request,
        "title": "SmartDesk Helpdesk",
        "year": datetime.now(timezone.utc).year,
        "roles": roles,
    }
    return templates.TemplateResponse("landing.html", context)


@router.get("/auth", response_class=HTMLResponse)
def auth_portal(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
):
    if current_user:
        return RedirectResponse(role_redirect(current_user.primary_role), status_code=status.HTTP_302_FOUND)

    mode = request.query_params.get("mode", "login")
    mode = "signup" if mode == "signup" else "login"

    roles = [
        {
            "value": role.value,
            "label": "SmartDesk Staff" if role == UserRole.smartdesk_staff else ("IT Manager" if role == UserRole.it_manager else "Requester"),
        }
        for role in UserRole
    ]

    context = {
        "request": request,
        "title": "Access SmartDesk",
        "mode": mode,
        "roles": roles,
        "year": datetime.now(timezone.utc).year,
    }
    return templates.TemplateResponse("auth.html", context)


@router.get("/desk", response_class=HTMLResponse)
def helpdesk(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
):
    context = {
        "request": request,
        "title": "SmartDesk Helpdesk",
        "issue_types": ISSUE_TYPES,
        "priorities": [priority.value for priority in TicketPriority],
        "statuses": [status.value for status in TicketStatus],
        "current_user": current_user,
    }
    return templates.TemplateResponse("index.html", context)


@router.get("/home", response_class=HTMLResponse)
def logged_in_home(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    context = {
        "request": request,
        "current_user": current_user,
        "year": datetime.now(timezone.utc).year,
        "role_home": role_redirect(current_user.primary_role),
    }
    return templates.TemplateResponse("home.html", context)


@router.get("/workspace", response_class=HTMLResponse)
def requester_workspace(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.requester)),
    db: Session = Depends(get_db),
):
    membership = get_primary_membership(db, current_user.id)
    organization = membership.organization if membership else None
    summary = ticket_service.user_ticket_summary(db, current_user.id)
    tickets = ticket_service.recent_user_tickets(db, current_user.id)
    context = {
        "request": request,
        "current_user": current_user,
        "organization": organization,
        "summary": summary,
        "tickets": tickets,
    }
    return templates.TemplateResponse("workspace.html", context)


@router.get("/manager", response_class=HTMLResponse)
def manager_dashboard(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.it_manager)),
    db: Session = Depends(get_db),
):
    membership = get_primary_membership(db, current_user.id)
    organization = membership.organization if membership else None
    organization_id = organization.id if organization else None
    summary = ticket_service.organization_ticket_summary(db, organization_id) if organization_id else {}
    tickets = (
        ticket_service.recent_organization_tickets(db, organization_id)
        if organization_id
        else []
    )
    recent_resolved = (
        ticket_service.resolved_in_period(db, organization_id, days=7)
        if organization_id
        else 0
    )
    context = {
        "request": request,
        "current_user": current_user,
        "organization": organization,
        "organization_plan": organization.plan if organization else "trial",
        "summary": summary,
        "tickets": tickets,
        "recent_resolved": recent_resolved,
    }
    return templates.TemplateResponse("manager.html", context)


@router.get("/admin/overview", response_class=HTMLResponse)
def admin_overview(
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    overview = platform_overview(db)
    organization_rows = (
        db.query(Organization, func.count(Membership.id))
        .outerjoin(Membership, Membership.organization_id == Organization.id)
        .group_by(Organization.id)
        .order_by(Organization.created_at.desc())
        .all()
    )
    organizations = [
        {
            "id": organization.id,
            "name": organization.name,
            "plan": organization.plan or "trial",
            "created_at": organization.created_at,
            "contact_email": organization.contact_email,
            "member_count": member_count,
        }
        for organization, member_count in organization_rows
    ]
    context = {
        "request": request,
        "current_user": current_user,
        "overview": overview,
        "organizations": organizations,
        "nav_active": "organizations",
    }
    return templates.TemplateResponse("admin_overview.html", context)


@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    overview = platform_overview(db)
    user_rows = (
        db.query(User, func.count(Membership.id))
        .outerjoin(Membership, Membership.user_id == User.id)
        .group_by(User.id)
        .order_by(User.created_at.desc())
        .all()
    )
    users = [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "primary_role": user.primary_role,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "member_count": member_count,
        }
        for user, member_count in user_rows
    ]
    context = {
        "request": request,
        "current_user": current_user,
        "overview": overview,
        "users": users,
        "nav_active": "users",
    }
    return templates.TemplateResponse("admin_users.html", context)
