from sqlmodel import create_engine, Session, SQLModel
from typing import Generator


DATABASE_URL = "sqlite:///database.db"


engine = create_engine(
    DATABASE_URL, echo=True, connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """Initializes the database and creates tables."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency to get a database session."""

    with Session(engine) as session:
        yield session
