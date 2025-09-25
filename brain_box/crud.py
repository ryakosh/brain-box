from sqlmodel import Session, func, select

from brain_box import models


def create_topic(session: Session, topic_in: models.TopicCreate) -> models.Topic:
    """Creates a new topic in the database.

    Args:
        session: The database session.
        topic_in: The data for the new topic.

    Returns:
        The newly created topic.
    """

    db_topic = models.Topic.model_validate(topic_in)

    session.add(db_topic)
    session.commit()
    session.refresh(db_topic)

    return db_topic


def get_topic(session: Session, topic_id: int) -> tuple[models.Topic, int] | None:
    """Retrieves a single topic by its ID.

    Args:
        session: The database session.
        topic_id: The ID of the topic to retrieve.

    Returns:
        A tuple consisting of the topic and count of entries respectively.
    """

    statement = select(models.Topic, _entries_count_subquery()).where(
        models.Topic.id == topic_id
    )

    result = session.exec(statement).first()

    if result is None:
        return

    return (
        result[0],
        result[1],
    )


def get_topics(
    session: Session, *, parent_id: int | None = None, skip: int = 0, limit: int = 100
) -> list[tuple[models.Topic, int]]:
    """Fetches a paginated list of topics.

    Args:
        session: The database session.
        parent_id: The ID of the parent topic.
        skip: The number of items to skip.
        limit: Limits the number of items returned.

    Returns:
        A tuple consisting of the topic and count of entries respectively.
    """

    statement = (
        select(models.Topic, _entries_count_subquery())
        .where(models.Topic.parent_id == parent_id)
        .order_by(models.Topic.name)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement).all()

    return list(results)


def update_topic(
    session: Session, topic: models.Topic, topic_in: models.TopicUpdate
) -> models.Topic:
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


def delete_topic(session: Session, topic: models.Topic) -> None:
    """Deletes a topic from the database.

    Args:
        session: The database session.
        topic: The topic model instance to delete.
    """

    session.delete(topic)
    session.commit()


def _entries_count_subquery():
    return (
        select(func.count(models.Entry.id))
        .where(models.Entry.topic_id == models.Topic.id)
        .correlate(models.Topic)
        .scalar_subquery()
    )


def create_entry(session: Session, entry_in: models.EntryCreate) -> models.Entry:
    """Creates a new learning entry in the database.

    Args:
        session: The database session.
        entry_in: The data for the new entry.

    Returns:
        The newly created entry model instance.
    """

    db_entry = models.Entry.model_validate(entry_in)

    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)

    return db_entry


def get_entry(session: Session, entry_id: int) -> models.Entry | None:
    """Retrieves a single entry by its ID.

    Args:
        session: The database session.
        entry_id: The ID of the entry to retrieve.

    Returns:
        The entry model instance or None if not found.
    """

    return session.get(models.Entry, entry_id)


def update_entry(
    session: Session, entry: models.Entry, entry_in: models.EntryUpdate
) -> models.Entry:
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


def delete_entry(session: Session, entry: models.Entry) -> None:
    """Deletes an entry from the database.

    Args:
        session: The database session.
        entry: The entry model instance to delete.
    """

    session.delete(entry)
    session.commit()


def search_topics(session: Session, q: str, limit: int = 10) -> list[models.Topic]:
    """
    Searches for topics by name with case-insensitive partial matching.

    Args:
        session: The database session.
        name: The partial name of the topic to search for.
        limit: The maximum number of topics to return.

    Returns:
        A list of matching Topic objects.
    """

    search_pattern = f"%{q.lower()}%"
    statement = (
        select(models.Topic)
        .where(func.lower(models.Topic.name).like(search_pattern))
        .limit(limit)
    )
    results = session.exec(statement).all()

    return list(results)
