from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


if TYPE_CHECKING:
    from brain_box.models.entry import Entry


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
        back_populates="parent", passive_deletes=True
    )
    entries: list["Entry"] = Relationship(back_populates="topic", passive_deletes=True)

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
    """Model for reading a topic and it's entries and subtopics count."""

    entries_count: int
    children_count: int
