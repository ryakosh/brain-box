from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlmodel import Session

from brain_box import crud
from brain_box.db import get_session
from brain_box.models.entry import EntryCreate, EntryRead, EntryUpdate
from brain_box.models.topic import (
    TopicCreate,
    TopicRead,
    TopicReadWithCounts,
    TopicUpdate,
)


api_router = APIRouter()


@api_router.post(
    "/topics/",
    response_model=TopicRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Topics"],
)
def create_topic(topic_in: TopicCreate, db: Session = Depends(get_session)):
    """Create a new topic."""

    try:
        return crud.create_topic(session=db, topic_in=topic_in)
    except crud.NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except crud.AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@api_router.get("/topics/sync", response_model=list[TopicRead], tags=["Topics"])
def sync_topics(
    *,
    db: Session = Depends(get_session),
):
    """Get a list of all topics."""

    return crud.sync_topics(session=db)


@api_router.get(
    "/topics/{topic_id}", response_model=TopicReadWithCounts, tags=["Topics"]
)
def read_topic(topic_id: int, db: Session = Depends(get_session)):
    """Retrieve a single topic by its ID."""

    result = crud.get_topic(session=db, topic_id=topic_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicReadWithCounts.model_validate(
        result[0],
        update={
            "entries_count": result[1],
            "children_count": result[2],
        },
    )


@api_router.get("/topics/", response_model=list[TopicReadWithCounts], tags=["Topics"])
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

    return [
        TopicReadWithCounts.model_validate(
            t, update={"entries_count": ec, "children_count": cc}
        )
        for t, ec, cc in results
    ]


@api_router.get("/topics/search/", response_model=list[TopicRead], tags=["Topics"])
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


@api_router.put("/topics/{topic_id}", response_model=TopicRead, tags=["Topics"])
def update_topic(
    topic_id: int, topic_in: TopicUpdate, db: Session = Depends(get_session)
):
    """Update a topic's name or change its parent."""

    result = crud.get_topic(session=db, topic_id=topic_id)

    if not result:
        raise HTTPException(status_code=404, detail="Topic not found")

    return crud.update_topic(session=db, topic=result[0], topic_in=topic_in)


@api_router.delete(
    "/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Topics"]
)
def delete_topic(topic_id: int, db: Session = Depends(get_session)):
    """Delete a topic."""

    db_topic = crud.get_topic(session=db, topic_id=topic_id)

    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    crud.delete_topic(session=db, topic=db_topic[0])

    return None


@api_router.post(
    "/entries/",
    response_model=EntryRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Entries"],
)
def create_entry(entry_in: EntryCreate, db: Session = Depends(get_session)):
    """Create a new  entry and associate it with a topic."""

    if not crud.get_topic(db, entry_in.topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")

    return crud.create_entry(session=db, entry_in=entry_in)


@api_router.get("/entries/{entry_id}", response_model=EntryRead, tags=["Entries"])
def read_entry(entry_id: int, db: Session = Depends(get_session)):
    """Retrieve a single  entry by its ID."""

    db_entry = crud.get_entry(session=db, entry_id=entry_id)

    if db_entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")

    return db_entry


@api_router.get("/entries/search/", response_model=list[EntryRead], tags=["Entries"])
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

    results = crud.search_entries(session=session, q=q, limit=limit, skip=skip)

    return results


@api_router.put("/entries/{entry_id}", response_model=EntryRead, tags=["Entries"])
def update_entry(
    entry_id: int, entry_in: EntryUpdate, db: Session = Depends(get_session)
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


@api_router.head("/health")
async def health_check():
    """
    Health check endpoint, returns 200 OK if the server is healthy.
    """

    return Response(status_code=200)
