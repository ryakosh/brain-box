import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from brain_box.db import get_session
from brain_box.main import app
from brain_box import models


DATABASE_URL = "sqlite:///test.db"


@pytest.fixture(scope="function", name="session")
def session_fixture():
    engine = create_engine(
        DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function", name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
