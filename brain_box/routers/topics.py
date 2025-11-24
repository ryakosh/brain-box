from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from brain_box.crud.errors import AlreadyExistsError, NotFoundError
from brain_box.db import get_session
from brain_box.models.topic import (
    TopicCreate,
    TopicRead,
    TopicReadWithCounts,
    TopicUpdate,
)
import brain_box.crud.topic as crud_topic

topics_router = APIRouter(prefix="/topics")


@topics_router.post(
    "/",
    response_model=TopicRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Topics"],
)
def create_topic(topic_in: TopicCreate, db: Session = Depends(get_session)):
    """Create a new topic."""

    try:
        return crud_topic.create_topic(session=db, topic_in=topic_in)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))


@topics_router.get("/sync", response_model=list[TopicRead], tags=["Topics"])
def sync_topics(
    *,
    db: Session = Depends(get_session),
):
    """Get a list of all topics."""

    return crud_topic.sync_topics(session=db)


@topics_router.get("/{topic_id}", response_model=TopicReadWithCounts, tags=["Topics"])
def read_topic(topic_id: int, db: Session = Depends(get_session)):
    """Retrieve a single topic by its ID."""

    result = crud_topic.get_topic(session=db, topic_id=topic_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicReadWithCounts.model_validate(
        result[0],
        update={
            "entries_count": result[1],
            "children_count": result[2],
        },
    )


@topics_router.get("/", response_model=list[TopicReadWithCounts], tags=["Topics"])
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

    results = crud_topic.get_topics(
        session=db, parent_id=parent_id, skip=skip, limit=limit
    )

    return [
        TopicReadWithCounts.model_validate(
            t, update={"entries_count": ec, "children_count": cc}
        )
        for t, ec, cc in results
    ]


@topics_router.get("/search/", response_model=list[TopicRead], tags=["Topics"])
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

    results = crud_topic.search_topics(session=db, q=q, limit=limit)

    return results


@topics_router.put("/{topic_id}", response_model=TopicRead, tags=["Topics"])
def update_topic(
    topic_id: int, topic_in: TopicUpdate, db: Session = Depends(get_session)
):
    """Update a topic's name or change its parent."""

    result = crud_topic.get_topic(session=db, topic_id=topic_id)

    if not result:
        raise HTTPException(status_code=404, detail="Topic not found")

    return crud_topic.update_topic(session=db, topic=result[0], topic_in=topic_in)


@topics_router.delete(
    "/{topic_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Topics"]
)
def delete_topic(topic_id: int, db: Session = Depends(get_session)):
    """Delete a topic."""

    db_topic = crud_topic.get_topic(session=db, topic_id=topic_id)

    if not db_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    crud_topic.delete_topic(session=db, topic=db_topic[0])

    return None
