from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from brain_box import crud, models
from brain_box.db import get_session


api_router = APIRouter(prefix="/api")


@api_router.post(
    "/topics/",
    response_model=models.TopicRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Topics"],
)
def create_topic(topic_in: models.TopicCreate, db: Session = Depends(get_session)):
    """Create a new topic."""

    if topic_in.parent_id and not crud.get_topic(db, topic_in.parent_id):
        raise HTTPException(status_code=404, detail="Parent topic not found")

    return crud.create_topic(session=db, topic_in=topic_in)


@api_router.get("/topics/{topic_id}", response_model=models.TopicRead, tags=["Topics"])
def read_topic(topic_id: int, db: Session = Depends(get_session)):
    """Retrieve a single topic by its ID."""

    db_topic = crud.get_topic(session=db, topic_id=topic_id)

    if db_topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    return db_topic


@api_router.get("/topics/", response_model=list[models.TopicRead], tags=["Topics"])
def read_topics(
    *,
    parent_id: int | None = Query(
        default=None, description="Filter by parent ID. Null for root topics."
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_session),
):
    """Get a list of topics with pagination, filterable by parent."""

    results = crud.get_topics(session=db, parent_id=parent_id, skip=skip, limit=limit)

    return results


@api_router.get(
    "/topics/search/", response_model=list[models.TopicRead], tags=["Topics"]
)
def search_topics(
    q: str = Query(
        ...,
        min_length=1,
        max_length=50,
        title="Search Query",
        description="The search term to look for in topics.",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of search results to return.",
    ),
    db: Session = Depends(get_session),
):
    """Search for topics by name with case-insensitive partial matching."""

    results = crud.search_topics(session=db, q=q, limit=limit)

    return results


@api_router.put("/topics/{topic_id}", response_model=models.TopicRead, tags=["Topics"])
def update_topic(
    topic_id: int, topic_in: models.TopicUpdate, db: Session = Depends(get_session)
):
    """Update a topic's name or change its parent."""

    db_topic = crud.get_topic(session=db, topic_id=topic_id)

    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    return crud.update_topic(session=db, topic=db_topic, topic_in=topic_in)


@api_router.delete(
    "/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Topics"]
)
def delete_topic(topic_id: int, db: Session = Depends(get_session)):
    """Delete a topic."""

    db_topic = crud.get_topic(session=db, topic_id=topic_id)

    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    crud.delete_topic(session=db, topic=db_topic)

    return None


@api_router.post(
    "/entries/",
    response_model=models.EntryRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Entries"],
)
def create_entry(entry_in: models.EntryCreate, db: Session = Depends(get_session)):
    """Create a new  entry and associate it with a topic."""

    if not crud.get_topic(db, entry_in.topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")

    return crud.create_entry(session=db, entry_in=entry_in)


@api_router.get(
    "/entries/{entry_id}", response_model=models.EntryRead, tags=["Entries"]
)
def read_entry(entry_id: int, db: Session = Depends(get_session)):
    """Retrieve a single  entry by its ID."""

    db_entry = crud.get_entry(session=db, entry_id=entry_id)

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    return db_entry


@api_router.put(
    "/entries/{entry_id}", response_model=models.EntryRead, tags=["Entries"]
)
def update_entry(
    entry_id: int, entry_in: models.EntryUpdate, db: Session = Depends(get_session)
):
    """Update an entry's description or move it to a different topic."""

    db_entry = crud.get_entry(session=db, entry_id=entry_id)

    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    return crud.update_entry(session=db, entry=db_entry, entry_in=entry_in)


@api_router.delete(
    "/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Entries"]
)
def delete_entry(entry_id: int, db: Session = Depends(get_session)):
    """Delete an entry."""

    db_entry = crud.get_entry(session=db, entry_id=entry_id)

    if not db_entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    crud.delete_entry(session=db, entry=db_entry)

    return None
