from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from brain_box.db import get_session
from brain_box.models.entry import EntryCreate, EntryRead, EntryUpdate
import brain_box.crud.topic as crud_topic
import brain_box.crud.entry as crud_entry

entries_router = APIRouter(prefix="/entries")


@entries_router.post(
    "/",
    response_model=EntryRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Entries"],
)
def create_entry(entry_in: EntryCreate, db: Session = Depends(get_session)):
    """Create a new  entry and associate it with a topic."""

    if not crud_topic.get_topic(db, entry_in.topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")

    return crud_entry.create_entry(session=db, entry_in=entry_in)


@entries_router.get("/{entry_id}", response_model=EntryRead, tags=["Entries"])
def read_entry(entry_id: int, db: Session = Depends(get_session)):
    """Retrieve a single  entry by its ID."""

    db_entry = crud_entry.get_entry(session=db, entry_id=entry_id)

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    return db_entry


@entries_router.get("/search/", response_model=list[EntryRead], tags=["Entries"])
def search_entries(
    session: Session = Depends(get_session),
    q: str = Query(
        ...,
        min_length=1,
        max_length=50,
        description="Search query string for entries.",
    ),
    limit: int = Query(default=10, ge=1, le=100),
    skip: int = Query(
        default=0,
        ge=0,
    ),
):
    """Search for entries."""

    results = crud_entry.search_entries(session=session, q=q, limit=limit, skip=skip)

    return results


@entries_router.put("/{entry_id}", response_model=EntryRead, tags=["Entries"])
def update_entry(
    entry_id: int, entry_in: EntryUpdate, db: Session = Depends(get_session)
):
    """Update an entry's description or move it to a different topic."""

    db_entry = crud_entry.get_entry(session=db, entry_id=entry_id)

    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return crud_entry.update_entry(session=db, entry=db_entry, entry_in=entry_in)


@entries_router.delete(
    "/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Entries"]
)
def delete_entry(entry_id: int, db: Session = Depends(get_session)):
    """Delete an entry."""

    db_entry = crud_entry.get_entry(session=db, entry_id=entry_id)

    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    crud_entry.delete_entry(session=db, entry=db_entry)

    return None
