from fastapi.testclient import TestClient
from sqlmodel import Session

from brain_box import models


def test_create_and_read_topic(client: TestClient):
    topic_data = {"name": "Software Development"}

    response_create = client.post("/api/topics/", json=topic_data)

    assert response_create.status_code == 201
    created_topic = response_create.json()
    assert created_topic["name"] == topic_data["name"]
    assert "id" in created_topic
    topic_id = created_topic["id"]

    response_read = client.get(f"/api/topics/{topic_id}")

    assert response_read.status_code == 200
    read_topic = response_read.json()
    assert read_topic["name"] == topic_data["name"]
    assert read_topic["id"] == topic_id


def test_create_hierarchical_topic(client: TestClient):
    parent_data = {"name": "Languages"}

    response_parent = client.post("/api/topics/", json=parent_data)

    assert response_parent.status_code == 201
    parent_id = response_parent.json()["id"]

    child_data = {"name": "Python", "parent_id": parent_id}

    response_child = client.post("/api/topics/", json=child_data)

    assert response_child.status_code == 201
    child_topic = response_child.json()
    assert child_topic["name"] == "Python"
    assert child_topic["parent_id"] == parent_id

    response_parent_detailed = client.get(f"/api/topics/{parent_id}")

    assert response_parent_detailed.status_code == 200
    parent_detailed = response_parent_detailed.json()
    assert len(parent_detailed["children"]) == 1
    assert parent_detailed["children"][0]["name"] == "Python"


def test_read_topic_not_found(client: TestClient):
    response = client.get("/api/topics/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Topic not found"


def test_search_topics_happy_path(client: TestClient, session: Session):
    session.add_all(
        [
            models.Topic(name="Python Programming"),
            models.Topic(name="JavaScript Essentials"),
            models.Topic(name="Another Python Topic"),
        ]
    )
    session.commit()

    response = client.get("/api/topics/search/?q=python")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    assert results[0]["name"] == "Python Programming"
    assert results[1]["name"] == "Another Python Topic"


def test_search_topics_case_insensitive(client: TestClient, session: Session):
    session.add(models.Topic(name="Cooking"))
    session.commit()

    response = client.get("/api/topics/search/?q=COOK")

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["name"] == "Cooking"


def test_search_topics_no_results(client: TestClient, session: Session):
    session.add(models.Topic(name="Go Language"))
    session.commit()

    response = client.get("/api/topics/search/?q=ruby")

    assert response.status_code == 200
    assert response.json() == []


def test_search_topics_uses_limit(client: TestClient, session: Session):
    session.add_all(
        [
            models.Topic(name="SQL Basics"),
            models.Topic(name="Advanced SQL"),
            models.Topic(name="NoSQL Databases"),
        ]
    )
    session.commit()

    response = client.get("/api/topics/search/?q=sql&limit=2")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_search_topics_validation_error_missing_q(client: TestClient):
    response = client.get("/api/topics/search/")

    assert response.status_code == 422


def test_search_topics_validation_error_q_too_short(client: TestClient):
    response = client.get("/api/topics/search/?q=")

    assert response.status_code == 422


def test_create_entry_for_topic(client: TestClient):
    topic_response = client.post("/api/topics/", json={"name": "Cooking"})
    topic_id = topic_response.json()["id"]

    entry_data = {
        "description": "Learned how to make a basic sauce.",
        "topic_id": topic_id,
    }

    response = client.post("/api/entries/", json=entry_data)

    assert response.status_code == 201
    entry = response.json()
    assert entry["description"] == entry_data["description"]
    assert entry["topic"]["id"] == topic_id


def test_delete_topic(client: TestClient):
    topic_response = client.post("/api/topics/", json={"name": "To Be Deleted"})
    assert topic_response.status_code == 201
    topic_id = topic_response.json()["id"]

    delete_response = client.delete(f"/api/topics/{topic_id}")

    assert delete_response.status_code == 204

    get_response = client.get(f"/api/topics/{topic_id}")

    assert get_response.status_code == 404
