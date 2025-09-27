from sqlmodel import create_engine, Session, SQLModel
from typing import Generator


DATABASE_URL = "sqlite:///database.db"


engine = create_engine(
    DATABASE_URL, echo=True, connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """Initializes the database and creates tables."""

    SQLModel.metadata.create_all(engine)

    create_fts = """
    CREATE VIRTUAL TABLE IF NOT EXISTS entry_fts
    USING fts5(description, tokenize = 'porter');
    """

    trigger_insert = """
    CREATE TRIGGER IF NOT EXISTS entry_ai AFTER INSERT ON entry BEGIN
        INSERT INTO entry_fts(rowid, description)
        VALUES (new.id, new.description);
    END;
    """

    trigger_delete = """
    CREATE TRIGGER IF NOT EXISTS entry_ad AFTER DELETE ON entry BEGIN
        DELETE FROM entry_fts WHERE rowid = old.id;
    END;
    """

    trigger_update = """
    CREATE TRIGGER IF NOT EXISTS entry_au AFTER UPDATE ON entry BEGIN
        DELETE FROM entry_fts WHERE rowid = old.id;
        INSERT INTO entry_fts(rowid, description)
        VALUES (new.id, new.description);
    END;
    """

    with engine.begin() as conn:
        conn.exec_driver_sql(create_fts)
        conn.exec_driver_sql(trigger_insert)
        conn.exec_driver_sql(trigger_delete)
        conn.exec_driver_sql(trigger_update)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency to get a database session."""

    with Session(engine) as session:
        yield session
