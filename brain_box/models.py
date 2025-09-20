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


class Entry(SQLModel, table=True):
    """Database model for an entry."""

    id: int | None = Field(default=None, primary_key=True)
    description: str = Field()
    created_at: datetime = Field(default_factory=utils.now)
    updated_at: datetime = Field(
        default_factory=utils.now,
        sa_column_kwargs={"onupdate": utils.now},
        nullable=False,
    )

    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="entries")
