from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    status: str


class APIKeyCreateRequest(BaseModel):
    project_id: str
    tag: str | None = None


class APIKeyResponse(BaseModel):
    id: str
    key_prefix: str
    tag: str | None
    status: str
    project_id: str
    owner_user_id: str | None
    created_by_user_id: str
    created_at: str
    last_used_at: str | None


class APIKeyCreateResponse(BaseModel):
    id: str
    key: str
    key_prefix: str
    tag: str | None
    status: str
    project_id: str
    owner_user_id: str | None
    created_by_user_id: str
    created_at: str


class AuthErrorResponse(BaseModel):
    error: dict
