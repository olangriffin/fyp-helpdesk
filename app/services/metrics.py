from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import User
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.ticket import Ticket


def platform_overview(db: Session) -> dict:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_memberships = db.query(func.count(Membership.id)).scalar() or 0
    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0

    verified_users = (
        db.query(func.count(User.id)).filter(User.email_verified == True).scalar()  # noqa: E712
    ) or 0

    return {
        "users": total_users,
        "verified_users": verified_users,
        "organizations": total_orgs,
        "memberships": total_memberships,
        "tickets": total_tickets,
    }


def recent_signups(db: Session, limit: int = 5) -> list[User]:
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .all()
    )


def recent_tickets(db: Session, limit: int = 10) -> list[Ticket]:
    return (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
        .all()
    )
