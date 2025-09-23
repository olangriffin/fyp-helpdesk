from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, event
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import TicketPriority, TicketStatus


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    issue_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default=TicketStatus.open.value)
    priority = Column(String, nullable=False, default=TicketPriority.medium.value)
    requester_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requester_name = Column(String, nullable=True)
    requester_email = Column(String, nullable=True)
    assignee_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="tickets")
    requester = relationship("User", foreign_keys=[requester_id], back_populates="requested_tickets")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tickets")


def _update_ticket_timestamp(mapper, connection, target) -> None:
    target.updated_at = datetime.now(timezone.utc)


event.listen(Ticket, "before_update", _update_ticket_timestamp)
