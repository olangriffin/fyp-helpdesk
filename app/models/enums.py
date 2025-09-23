from enum import Enum


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    waiting = "waiting_for_customer"
    resolved = "resolved"


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class UserRole(str, Enum):
    requester = "requester"
    it_manager = "it_manager"
    smartdesk_staff = "smartdesk_staff"
