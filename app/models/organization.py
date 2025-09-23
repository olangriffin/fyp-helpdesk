from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, event
from sqlalchemy.orm import relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False, unique=True)
    slug = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    domain = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    plan = Column(String, nullable=True, default="trial")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="organization")


def _update_organization_timestamp(mapper, connection, target) -> None:
    target.updated_at = datetime.now(timezone.utc)


event.listen(Organization, "before_update", _update_organization_timestamp)
