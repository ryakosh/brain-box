from sqlalchemy import text
from sqlmodel import Session

from brain_box.models.entry import Entry, EntryCreate, EntryUpdate
from brain_box.models.topic import Topic
from brain_box.utils import sanitize_alnum


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
