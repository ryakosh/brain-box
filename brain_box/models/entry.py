from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from brain_box import utils


if TYPE_CHECKING:
    from brain_box.models.topic import Topic, TopicRead


class Entry(SQLModel, table=True):
    """Database model for an entry."""

    id: int | None = Field(default=None, primary_key=True)
    description: str
    created_at: datetime = Field(default_factory=utils.now)
    updated_at: datetime = Field(
        default_factory=utils.now,
        sa_column_kwargs={"onupdate": utils.now},
        nullable=False,
    )

    topic_id: int = Field(foreign_key="topic.id", index=True, ondelete="CASCADE")
    topic: "Topic" = Relationship(back_populates="entries")


class EntryCreate(SQLModel):
    """Model for creating a new entry."""

    description: str
    topic_id: int


class EntryUpdate(SQLModel):
    """Model for updating an existing entry."""

    description: str | None = None
    topic_id: int | None = None


class EntryRead(SQLModel):
    """Model for reading an entry."""

    id: int
    description: str
    topic: "TopicRead"
