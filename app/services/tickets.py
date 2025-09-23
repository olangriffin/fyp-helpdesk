from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import TicketPriority, TicketStatus
from app.models.ticket import Ticket as TicketModel
from app.schemas.ticket import TicketCreate, TicketUpdate

ISSUE_TYPES = [
    "login_issue",
    "network",
    "hardware",
    "software_bug",
    "billing",
    "other",
]

_AUTO_RESOLUTION_RULES: Dict[str, str] = {
    "password reset": "Reset the password via the self-service portal and advise the requester to update credentials.",
    "vpn": "Restart the VPN client, verify network connectivity, and retry with the latest configuration file.",
    "printer": "Restart the printer service and confirm the device is on the corporate network. Job should complete afterward.",
}


def _coerce_enum(value, enum_cls):
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value.value
    return value


def _auto_resolve(payload: TicketCreate) -> Optional[str]:
    combined = " ".join(
        part
        for part in [payload.subject, payload.description, payload.additional_context or ""]
        if part
    ).lower()
    for keyword, resolution in _AUTO_RESOLUTION_RULES.items():
        if keyword in combined:
            return resolution
    return None


def list_tickets(db: Session, organization_id: Optional[str] = None) -> List[TicketModel]:
    query = db.query(TicketModel)
    if organization_id:
        query = query.filter(TicketModel.organization_id == organization_id)
    return query.order_by(TicketModel.created_at.desc()).all()


def get_ticket(db: Session, ticket_id: str) -> Optional[TicketModel]:
    return db.query(TicketModel).filter(TicketModel.id == ticket_id).first()


def create_ticket(db: Session, payload: TicketCreate) -> TicketModel:
    resolution = _auto_resolve(payload)

    ticket = TicketModel(
        organization_id=payload.organization_id,
        subject=payload.subject,
        description=payload.description,
        issue_type=payload.issue_type,
        priority=_coerce_enum(payload.priority, TicketPriority) or TicketPriority.medium.value,
        status=TicketStatus.resolved.value if resolution else TicketStatus.open.value,
        requester_id=payload.requester_id,
        requester_name=payload.requester_name,
        requester_email=payload.requester_email,
        assignee_id=payload.assignee_id,
        resolution_notes=resolution,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def update_ticket(db: Session, ticket_id: str, payload: TicketUpdate) -> TicketModel:
    ticket = get_ticket(db, ticket_id)
    if not ticket:
        raise KeyError("Ticket not found")

    if payload.status is not None:
        ticket.status = _coerce_enum(payload.status, TicketStatus)
    if payload.assignee_id is not None:
        ticket.assignee_id = payload.assignee_id
    if payload.priority is not None:
        ticket.priority = _coerce_enum(payload.priority, TicketPriority)
    if payload.resolution_notes is not None:
        ticket.resolution_notes = payload.resolution_notes

    db.commit()
    db.refresh(ticket)
    return ticket


def ticket_stats(db: Session, organization_id: Optional[str] = None) -> Dict[str, Dict[str, int]]:
    query = db.query(TicketModel)
    if organization_id:
        query = query.filter(TicketModel.organization_id == organization_id)

    tickets = query.all()
    status_counts: Counter = Counter(ticket.status for ticket in tickets)
    priority_counts: Counter = Counter(ticket.priority for ticket in tickets)
    issue_counts: Counter = Counter(ticket.issue_type for ticket in tickets)

    return {
        "status": dict(status_counts),
        "priority": dict(priority_counts),
        "issue_type": dict(issue_counts),
        "total": {"tickets": len(tickets)},
    }


def ticket_status_summary(db: Session, organization_id: Optional[str] = None) -> Dict[str, int]:
    query = db.query(TicketModel.status, func.count(TicketModel.id)).group_by(TicketModel.status)
    if organization_id:
        query = query.filter(TicketModel.organization_id == organization_id)
    results = query.all()
    return {status: count for status, count in results}


def user_ticket_summary(db: Session, user_id: str) -> Dict[str, int]:
    results = (
        db.query(TicketModel.status, func.count(TicketModel.id))
        .filter(TicketModel.requester_id == user_id)
        .group_by(TicketModel.status)
        .all()
    )
    total = sum(count for _, count in results)
    return {"total": total, **{status: count for status, count in results}}


def recent_user_tickets(db: Session, user_id: str, limit: int = 6) -> List[TicketModel]:
    return (
        db.query(TicketModel)
        .filter(TicketModel.requester_id == user_id)
        .order_by(TicketModel.updated_at.desc())
        .limit(limit)
        .all()
    )


def organization_ticket_summary(db: Session, organization_id: str) -> Dict[str, int]:
    results = (
        db.query(TicketModel.status, func.count(TicketModel.id))
        .filter(TicketModel.organization_id == organization_id)
        .group_by(TicketModel.status)
        .all()
    )
    total = sum(count for _, count in results)
    return {"total": total, **{status: count for status, count in results}}


def recent_organization_tickets(
    db: Session,
    organization_id: str,
    limit: int = 8,
) -> List[TicketModel]:
    return (
        db.query(TicketModel)
        .filter(TicketModel.organization_id == organization_id)
        .order_by(TicketModel.updated_at.desc())
        .limit(limit)
        .all()
    )


def resolved_in_period(
    db: Session,
    organization_id: str,
    days: int = 7,
) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return (
        db.query(func.count(TicketModel.id))
        .filter(
            TicketModel.organization_id == organization_id,
            TicketModel.status == TicketStatus.resolved.value,
            TicketModel.updated_at >= cutoff,
        )
        .scalar()
        or 0
    )
