from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
import uuid
from datetime import datetime, timezone


class UserRole:
    ADMIN = "admin"
    SITE_ENGINEER = "site_engineer"
    FINANCE = "finance"
    PROCUREMENT = "procurement"


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = UserRole.SITE_ENGINEER
    phone: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class UserRoleAssign(BaseModel):
    role: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str
