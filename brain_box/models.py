from typing import Optional
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from brain_box import utils


class Topic(SQLModel, table=True):
    """Database model for a topic."""

    id: int | None = Field(default=None, primary_key=True)
    name: str

    parent_id: int | None = Field(
        default=None,
        nullable=True,
        foreign_key="topic.id",
        index=True,
        ondelete="CASCADE",
    )
    parent: Optional["Topic"] = Relationship(
        back_populates="children", sa_relationship_kwargs=dict(remote_side="Topic.id")
    )
    children: list["Topic"] = Relationship(
        back_populates="parent", sa_relationship_kwargs={"passive_deletes": True}
    )
    entries: list["Entry"] = Relationship(
        back_populates="topic", sa_relationship_kwargs={"passive_deletes": True}
    )

    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_topic_name_parent_id"),
    )


class TopicCreate(SQLModel):
    """Model for creating a new topic."""

    name: str
    parent_id: int | None = Field(default=None, ge=1)


class TopicUpdate(SQLModel):
    """Model for updating an existing topic."""

    name: str | None = None
    parent_id: int | None = None


class TopicParentInfo(SQLModel):
    """Model for reading info of parent topic."""

    name: str
    parent_id: int | None


class TopicRead(SQLModel):
    """Model for reading a topic."""

    id: int
    name: str
    parent_id: int | None
    parent: TopicParentInfo | None


class TopicReadWithCounts(TopicRead):
    entries_count: int
    children_count: int


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
    topic: Topic = Relationship(back_populates="entries")


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
    topic: TopicRead
