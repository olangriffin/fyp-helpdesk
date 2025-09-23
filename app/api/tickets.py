from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.services import tickets as ticket_service

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/", response_model=List[TicketRead])
def list_tickets(
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return ticket_service.list_tickets(db, organization_id)


@router.get("/stats")
def ticket_stats(
    organization_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return ticket_service.ticket_stats(db, organization_id)


@router.post("/", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    return ticket_service.create_ticket(db, payload)


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(ticket_id: str, payload: TicketUpdate, db: Session = Depends(get_db)):
    try:
        return ticket_service.update_ticket(db, ticket_id, payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found") from None


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = ticket_service.get_ticket(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket
