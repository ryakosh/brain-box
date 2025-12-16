import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

from brain_box import utils


class RefreshToken(SQLModel, table=True):
    """Database model for a refresh token."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hash: str = Field(unique=True)
    expires_at: datetime = Field(index=True)
    created_at: datetime = Field(default_factory=utils.now)


class RefreshTokenCreate(SQLModel):
    """Model for creating a new refresh token."""

    hash: str
    expires_at: datetime


class AccessTokenRead(BaseModel):
    """Access token response model."""

    token: str
    token_type: str
    expires_in: int
