from fastapi.testclient import TestClient


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
