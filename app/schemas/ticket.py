from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict

from app.models.enums import TicketPriority, TicketStatus


class TicketBase(BaseModel):
    subject: str = Field(..., min_length=3, max_length=120)
    description: str = Field(..., min_length=10, max_length=5000)
    issue_type: str = Field(..., min_length=3)
    priority: TicketPriority = TicketPriority.medium
    additional_context: Optional[str] = None


class TicketCreate(TicketBase):
    organization_id: Optional[str] = None
    requester_id: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[EmailStr] = None
    assignee_id: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    assignee_id: Optional[str] = None
    resolution_notes: Optional[str] = None
    priority: Optional[TicketPriority] = None


class TicketRead(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: Optional[str] = None
    requester_id: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[EmailStr] = None
    assignee_id: Optional[str] = None
    status: TicketStatus
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
