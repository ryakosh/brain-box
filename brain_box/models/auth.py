from datetime import datetime
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from brain_box import utils


class RefreshToken(SQLModel, table=True):
    """Database model for a refresh token."""

    id: UUID = Field(primary_key=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=utils.now)


class RefreshTokenCreate(SQLModel):
    """Model for creating a new refresh token."""

    id: UUID
    expires_at: datetime


class AccessTokenRead(BaseModel):
    """Access token response model."""

    token: str
    token_type: str
