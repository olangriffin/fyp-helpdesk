from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict

from app.models.enums import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    primary_role: UserRole = UserRole.requester
    organization_name: Optional[str] = None
    organization_slug: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: Optional[str]
    primary_role: UserRole
    email_verified: bool


class EmailVerificationRequest(BaseModel):
    token: str = Field(..., min_length=10)


class ResendVerificationRequest(BaseModel):
    email: EmailStr
