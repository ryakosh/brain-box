from sqlalchemy.orm import aliased
from sqlmodel import Session, func, select

from brain_box.crud.errors import AlreadyExistsError, NotFoundError
from brain_box.models.entry import Entry
from brain_box.models.topic import Topic, TopicCreate, TopicUpdate


def create_topic(session: Session, topic_in: TopicCreate) -> Topic:
    """Creates a new topic in the database.

    Args:
        session: The database session.
        topic_in: The data for the new topic.

    Returns:
        The newly created topic.
    """

    topic_with_same_name = select(Topic).where(
        func.lower(Topic.name) == topic_in.name.lower(),
        Topic.parent_id == topic_in.parent_id,
    )

    parent_topic = select(Topic).where(Topic.id == topic_in.parent_id)

    if session.exec(topic_with_same_name).first():
        raise AlreadyExistsError("Topic name already in use")

    if topic_in.parent_id and not session.exec(parent_topic).first():
        raise NotFoundError("Parent topic not found")

    db_topic = Topic.model_validate(topic_in)

    session.add(db_topic)
    session.commit()
    session.refresh(db_topic)

    return db_topic


def get_topic(session: Session, topic_id: int) -> tuple[Topic, int, int] | None:
    """Retrieves a single topic with its children and entry counts.

    Args:
        session: The database session.
        topic_id: The ID of the topic to retrieve.

    Returns:
        A tuple, which contains:
        (Topic object, count of its entries, count of its children).
    """

    ParentTopic = aliased(Topic, name="parent_topic")
    ChildTopic = aliased(Topic, name="child_topic")

    statement = select(
        ParentTopic,
        _topic_entries_subquery(ParentTopic, Entry),
        _topic_children_subquery(ParentTopic, ChildTopic),
    ).where(ParentTopic.id == topic_id)

    result = session.exec(statement).first()

    if result is None:
        return None

    return result


def get_topics(
    session: Session, *, parent_id: int | None = None, skip: int = 0, limit: int = 100
) -> list[tuple[Topic, int, int]]:
    """Fetches a paginated list of topics with their children and entry counts.

    Args:
        session: The database session.
        parent_id: The ID of the parent topic to filter by. If None, fetches root topics.
        skip: The number of records to skip (for pagination).
        limit: The maximum number of records to return.

    Returns:
        A list of tuples, where each tuple contains:
        (Topic object, count of its entries, count of its children).
    """

    ParentTopic = aliased(Topic, name="parent_topic")
    ChildTopic = aliased(Topic, name="child_topic")

    statement = (
        select(
            ParentTopic,
            _topic_entries_subquery(ParentTopic, Entry),
            _topic_children_subquery(ParentTopic, ChildTopic),
        )
        .where(ParentTopic.parent_id == parent_id)
        .order_by(func.lower(ParentTopic.name))
        .offset(skip)
        .limit(limit)
    )

    results = session.exec(statement).all()

    return list(results)


def sync_topics(session: Session) -> list[Topic]:
    """
    Get all the available topics.

    Args:
        session: The database session.

    Returns:
        A list of all Topic objects.
    """

    statement = select(Topic)
    results = session.exec(statement).all()

    return list(results)


def update_topic(session: Session, topic: Topic, topic_in: TopicUpdate) -> Topic:
    """Updates an existing topic in the database.

    Args:
        session: The database session.
        topic: The existing topic model instance to update.
        topic_in: The new data for the topic.

    Returns:
        The updated topic model instance.
    """

    topic_data = topic_in.model_dump(exclude_unset=True)

    topic.sqlmodel_update(topic_data)
    session.add(topic)
    session.commit()
    session.refresh(topic)

    return topic


def delete_topic(session: Session, topic: Topic) -> None:
    """Deletes a topic from the database.

    Args:
        session: The database session.
        topic: The topic model instance to delete.
    """

    session.delete(topic)
    session.commit()


def _topic_entries_subquery(ParentTopic, Entry):
    return (
        select(func.count(Entry.id))
        .where(Entry.topic_id == ParentTopic.id)
        .correlate(ParentTopic)
        .scalar_subquery()
        .label("entries_count")
    )


def _topic_children_subquery(ParentTopic, ChildTopic):
    return (
        select(func.count(ChildTopic.id))
        .where(ChildTopic.parent_id == ParentTopic.id)
        .correlate(ParentTopic)
        .scalar_subquery()
        .label("children_count")
    )


def search_topics(session: Session, q: str, limit: int = 10) -> list[Topic]:
    """
    Searches for topics.

    Args:
        session: The database session.
        q: The search string.
        limit: The maximum number of topics to return.

    Returns:
        A list of matching Topic objects.
    """

    search_pattern = f"%{q.lower()}%"
    statement = (
        select(Topic).where(func.lower(Topic.name).like(search_pattern)).limit(limit)
    )
    results = session.exec(statement).all()

    return list(results)
