"""
Pydantic schemas for request/response validation
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, validator


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response data."""
    id: int
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        orm_mode = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    """Schema for token data."""
    email: Optional[str] = None


class HealthCheck(BaseModel):
    """Schema for health check response."""
    status: str
    timestamp: str
    service: str
    version: str 