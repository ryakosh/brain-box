from typing import cast
from fastapi.testclient import TestClient
from sqlmodel import Session

from brain_box import models


def test_create_and_read_entry(client: TestClient, session: Session):
    topic = models.Topic(name="Cooking")
    session.add(topic)
    session.commit()
    session.refresh(topic)

    entry_data = {
        "description": "Learned how to make a basic sauce.",
        "topic_id": topic.id,
    }

    response = client.post("/api/entries/", json=entry_data)

    assert response.status_code == 201
    entry = response.json()
    assert entry["description"] == entry_data["description"]
    assert entry["topic"]["id"] == topic.id


def test_search_entries(client: TestClient, session: Session):
    topic = models.Topic(name="Cooking")
    session.add(topic)
    session.commit()
    session.refresh(topic)

    entry_data = {
        "description": "Learned how to make a basic sauce.",
        "topic_id": topic.id,
    }

    entry = models.Entry(**entry_data)
    session.add(entry)
    session.commit()

    search_response = client.get("/api/entries/search/", params={"q": "basic"})
    search_response_data = search_response.json()

    assert search_response.status_code == 200
    assert len(search_response_data) == 1


def test_search_entries_non_existing_entry(client: TestClient, session: Session):
    topic = models.Topic(name="Cooking")
    session.add(topic)
    session.commit()
    session.refresh(topic)

    entry_data = {
        "description": "Learned how to make a basic sauce.",
        "topic_id": topic.id,
    }

    entry = models.Entry(**entry_data)
    session.add(entry)
    session.commit()

    search_response = client.get("/api/entries/search/", params={"q": "42"})
    search_response_data = search_response.json()

    assert search_response.status_code == 200
    assert len(search_response_data) == 0


def test_search_entries_multiple_term(client: TestClient, session: Session):
    topic = models.Topic(name="Cooking")
    session.add(topic)
    session.commit()
    session.refresh(topic)

    entry_data = {
        "description": "Learned how to make a basic sauce.",
        "topic_id": topic.id,
    }

    entry = models.Entry(**entry_data)
    session.add(entry)
    session.commit()

    search_response = client.get("/api/entries/search/", params={"q": "how sauce"})
    search_response_data = search_response.json()

    assert search_response.status_code == 200
    assert len(search_response_data) == 1


def test_search_entries_multiple_results(client: TestClient, session: Session):
    topic = models.Topic(name="Cooking")
    session.add(topic)
    session.commit()
    session.refresh(topic)
    topic_id: int = cast(int, topic.id)

    entries_data = [
        models.Entry(
            description="Learned how to make a basic sauce.",
            topic_id=topic_id,
        ),
        models.Entry(
            description="This sauce thing is good.",
            topic_id=topic_id,
        ),
        models.Entry(
            description="Mmm, this apple tastes good.",
            topic_id=topic_id,
        ),
    ]

    session.add_all(entries_data)
    session.commit()

    search_response = client.get("/api/entries/search/", params={"q": "sauce"})
    search_response_data = search_response.json()

    assert search_response.status_code == 200
    assert len(search_response_data) == 2


def test_delete_entry(client: TestClient, session: Session):
    topic = models.Topic(name="Cooking")
    session.add(topic)
    session.commit()
    session.refresh(topic)

    entry_data = {
        "description": "Learned how to make a basic saucee.",
        "topic_id": topic.id,
    }

    entry = models.Entry(**entry_data)
    session.add(entry)
    session.commit()
    session.refresh(entry)

    delete_response = client.delete(f"/api/entries/{entry.id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/entries/{entry.id}")
    assert get_response.status_code == 404
