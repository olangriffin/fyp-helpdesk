from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Text, event
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    password_salt = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    department = Column(String, nullable=True)
    primary_role = Column(String, nullable=False, default=UserRole.requester.value)
    role_overrides = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True, index=True)
    verification_sent_at = Column(DateTime, nullable=True)
    password_updated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    profile_complete = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    requested_tickets = relationship("Ticket", back_populates="requester", foreign_keys="Ticket.requester_id")
    assigned_tickets = relationship("Ticket", back_populates="assignee", foreign_keys="Ticket.assignee_id")


def _update_user_timestamp(mapper, connection, target) -> None:
    target.updated_at = datetime.now(timezone.utc)


event.listen(User, "before_update", _update_user_timestamp)
