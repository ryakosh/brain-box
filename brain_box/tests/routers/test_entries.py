from fastapi.testclient import TestClient
from sqlmodel import Session

from brain_box import models


def test_create_and_read_entry(client: TestClient):
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


def test_delete_entry(client: TestClient):
    topic_response = client.post("/api/topics/", json={"name": "Cooking"})
    topic_id = topic_response.json()["id"]

    entry_data = {
        "description": "Learned how to make a basic sauce.",
        "topic_id": topic_id,
    }

    entry_response = client.post("/api/entries/", json=entry_data)
    entry_response_data = entry_response.json()
    assert entry_response.status_code == 201

    delete_response = client.delete(f"/api/entries/{entry_response_data['id']}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/entries/{entry_response_data['id']}")
    assert get_response.status_code == 404
