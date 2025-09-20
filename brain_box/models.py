from __future__ import annotations
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from brain_box import utils


class Topic(SQLModel, table=True):
    """Database model for a topic."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)

    parent_id: int | None = Field(default=None, foreign_key="topic.id")
    parent: Topic | None = Relationship(back_populates="children")
    children: list[Topic] = Relationship(back_populates="parent")
    entries: list[Entry] = Relationship(back_populates="topic")


class TopicCreate(SQLModel):
    """Model for creating a new topic."""

    name: str
    parent_id: int | None = None


class TopicUpdate(SQLModel):
    """Model for updating an existing topic."""

    name: str | None = None
    parent_id: int | None = None


class TopicRead(SQLModel):
    """Model for reading a topic."""

    id: int
    name: str
    parent_id: int | None


class TopicReadWithDetails(TopicRead):
    """Model for reading a topic with its nested children and entries."""

    children: list[TopicRead] = []


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

    topic_id: int = Field(foreign_key="topic.id")
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
