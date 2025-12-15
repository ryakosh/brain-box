from sqlmodel import Session

from brain_box.models.auth import RefreshToken, RefreshTokenCreate


def create_refresh_token(
    session: Session, refresh_token_in: RefreshTokenCreate
) -> RefreshToken:
    """Creates a new refresh token in the database.

    Args:
        session: The database session.
        refresh_token_in: The data for the new refresh token.

    Returns:
        The newly created refresh token.
    """

    db_refresh_token = RefreshToken.model_validate(refresh_token_in)

    session.add(db_refresh_token)
    session.commit()
    session.refresh(db_refresh_token)

    return db_refresh_token


def get_refresh_token(session: Session, refresh_token_id: int) -> RefreshToken | None:
    """Retrieves a single refresh token.

    Args:
        session: The database session.
        refresh_token_id: The ID of the refresh token to retrieve.

    Returns:
        The refresh token model instance or None if not found.
    """

    result = session.get(RefreshToken, refresh_token_id)

    if result is None:
        return

    return result


def delete_refresh_token(session: Session, refresh_token: RefreshToken) -> None:
    """Deletes a refresh token from the database.

    Args:
        session: The database session.
        refresh_token: The refresh token model instance to delete.
    """

    session.delete(refresh_token)
    session.commit()
