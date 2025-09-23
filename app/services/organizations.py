from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.models.organization import Organization


def list_organizations(db: Session) -> list[Organization]:
    return db.query(Organization).order_by(Organization.created_at.desc()).all()


def get_organization(db: Session, organization_id: str) -> Optional[Organization]:
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_organization_by_slug(db: Session, slug: str) -> Optional[Organization]:
    return db.query(Organization).filter(Organization.slug == slug).first()


def create_organization(
    db: Session,
    *,
    name: str,
    slug: str,
    description: Optional[str] = None,
    domain: Optional[str] = None,
    contact_email: Optional[str] = None,
    plan: Optional[str] = None,
) -> Organization:
    organization = Organization(
        name=name,
        slug=slug,
        description=description,
        domain=domain,
        contact_email=contact_email,
        plan=plan or "trial",
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


def add_or_update_membership(
    db: Session,
    *,
    user_id: str,
    organization_id: str,
    role: str,
    is_owner: bool = False,
) -> Membership:
    membership = (
        db.query(Membership)
        .filter(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
        )
        .first()
    )
    if membership:
        membership.role = role
        membership.is_owner = is_owner
        membership.is_active = True
    else:
        membership = Membership(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            is_owner=is_owner,
        )
        db.add(membership)

    db.commit()
    db.refresh(membership)
    return membership


def organization_summary(db: Session) -> dict[str, int]:
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_memberships = db.query(func.count(Membership.id)).scalar() or 0
    return {
        "organizations": total_orgs,
        "memberships": total_memberships,
    }


def get_active_memberships(db: Session, user_id: str) -> list[Membership]:
    return (
        db.query(Membership)
        .filter(Membership.user_id == user_id, Membership.is_active == True)  # noqa: E712
        .order_by(Membership.created_at.asc())
        .all()
    )


def get_primary_membership(db: Session, user_id: str) -> Optional[Membership]:
    memberships = get_active_memberships(db, user_id)
    return memberships[0] if memberships else None
