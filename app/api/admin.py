from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.dependencies.auth import require_roles
from app.models import User
from app.models.enums import TicketPriority, TicketStatus, UserRole
from app.services import tickets as ticket_service

router = APIRouter(tags=["admin"])


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    current_user: User = Depends(require_roles(UserRole.it_manager, UserRole.smartdesk_staff)),
):
    stats = ticket_service.ticket_stats()
    context = {
        "request": request,
        "title": "SmartDesk Management",
        "statuses": [status.value for status in TicketStatus],
        "priorities": [priority.value for priority in TicketPriority],
        "stats": stats,
        "current_user": current_user,
    }
    return templates.TemplateResponse("admin.html", context)
