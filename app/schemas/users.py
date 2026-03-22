from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr


# What we expect when someone registers
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


# What we expect when someone logs in
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# What we send back when returning user data
# Notice: no password field — we never send that back
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# What we send back after a successful login
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# What we allow users to update about themselves
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None