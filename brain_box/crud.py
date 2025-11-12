from sqlalchemy import text
from sqlalchemy.orm import aliased
from sqlmodel import Session, func, select

from brain_box.models.entry import Entry, EntryCreate, EntryUpdate
from brain_box.models.topic import Topic, TopicCreate, TopicUpdate
from brain_box.utils import sanitize_alnum


class CRUDError(Exception):
    pass


class AlreadyExistsError(CRUDError):
    pass


class NotFoundError(CRUDError):
    pass


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
        return

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


def create_entry(session: Session, entry_in: EntryCreate) -> Entry:
    """Creates a new learning entry in the database.

    Args:
        session: The database session.
        entry_in: The data for the new entry.

    Returns:
        The newly created entry model instance.
    """

    db_entry = Entry.model_validate(entry_in)

    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)

    return db_entry


def get_entry(session: Session, entry_id: int) -> Entry | None:
    """Retrieves a single entry by its ID.

    Args:
        session: The database session.
        entry_id: The ID of the entry to retrieve.

    Returns:
        The entry model instance or None if not found.
    """

    return session.get(Entry, entry_id)


def update_entry(session: Session, entry: Entry, entry_in: EntryUpdate) -> Entry:
    """Updates an existing entry in the database.

    Args:
        session: The database session.
        entry: The existing entry model instance to update.
        entry_in: The new data for the entry.

    Returns:
        The updated entry model instance.
    """

    entry_data = entry_in.model_dump(exclude_unset=True)

    entry.sqlmodel_update(entry_data)
    session.add(entry)
    session.commit()
    session.refresh(entry)

    return entry


def delete_entry(session: Session, entry: Entry) -> None:
    """Deletes an entry from the database.

    Args:
        session: The database session.
        entry: The entry model instance to delete.
    """

    session.delete(entry)
    session.commit()


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


def search_entries(
    session: Session, q: str, limit: int = 25, skip: int = 0
) -> list[Entry]:
    """Searches for entries.

    Args:
        session: The database session.
        q: The search string.
        limit: The maximum number of entries to return.
        skip: The number of records to skip (for pagination).

    Returns:
        A list of matching Entry model instances.
    """

    query_sql = text("""
        SELECT e.id, snippet(entry_fts, -1, '<b>', '</b>', '...', 20) AS description, e.created_at, e.updated_at, e.topic_id, t.name, t.parent_id
        FROM entry e
        JOIN topic t ON t.id = e.topic_id
        JOIN entry_fts ON e.id = entry_fts.rowid
        WHERE entry_fts MATCH :query
        LIMIT :limit OFFSET :offset
    """)

    result = session.connection().execute(
        query_sql,
        {"query": f"{sanitize_alnum(q.strip())}*", "limit": limit, "offset": skip},
    )

    rows = result.fetchall()
    entries = [
        Entry(
            id=row.id,
            description=row.description,
            created_at=row.created_at,
            updated_at=row.updated_at,
            topic_id=row.topic_id,
            topic=Topic(id=row.topic_id, name=row.name, parent_id=row.parent_id),
        )
        for row in rows
    ]

    return entries
