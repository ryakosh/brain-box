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


def test_read_topic_not_found(client: TestClient):
    response = client.get("/api/topics/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Topic not found"


def test_read_topics_returns_root_topics_by_default(
    client: TestClient, session: Session
):
    root1 = models.Topic(name="Root A")
    root2 = models.Topic(name="Root B")
    session.add_all([root1, root2])
    session.commit()
    session.refresh(root1)

    child1 = models.Topic(name="Child A1", parent_id=root1.id)
    session.add(child1)
    session.commit()

    response = client.get("/api/topics/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d["name"] for d in data} == {"Root A", "Root B"}


def test_read_topics_filters_by_parent_id(client: TestClient, session: Session):
    root = models.Topic(name="Root")
    session.add(root)
    session.commit()
    session.refresh(root)

    child1 = models.Topic(name="Child 1", parent_id=root.id)
    child2 = models.Topic(name="Child 2", parent_id=root.id)
    session.add_all([child1, child2])
    session.commit()

    response = client.get(f"/api/topics/?parent_id={root.id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d["name"] for d in data} == {"Child 1", "Child 2"}


def test_read_topics_pagination(client: TestClient, session: Session):
    session.add_all([models.Topic(name=f"Topic {i}") for i in range(5)])
    session.commit()

    response = client.get("/api/topics/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Topic 0"

    response = client.get("/api/topics/?limit=2&skip=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Topic 2"


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


def test_delete_topic(client: TestClient):
    topic_response = client.post("/api/topics/", json={"name": "To Be Deleted"})
    assert topic_response.status_code == 201
    topic_id = topic_response.json()["id"]

    delete_response = client.delete(f"/api/topics/{topic_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/topics/{topic_id}")
    assert get_response.status_code == 404
