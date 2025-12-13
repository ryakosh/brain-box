from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from pwdlib import PasswordHash

from brain_box.config import settings


class Token(BaseModel):
    token: str
    token_type: str


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify provided password against the hashed password.

    Args:
        plain_password: Plain user provided password.
        hashed_password: Hashed password.

    Returns:
        `True` if verification was successful, `False` otherwise.
    """

    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates hash for `password`.

    Args:
        password: Plain user provided password.

    Returns:
        The hashed version of the `password`.
    """

    return password_hash.hash(password)


def verify_user(username: str, password: str) -> bool:
    """Verifies whether user are who they claim they are.

    Args:
        username: The provided username.
        password: The provided password.

    Returns:
        `True` if verification was successful, `False` otherwise.
    """

    hashed_password = settings.security.hashed_password

    if hashed_password is None or hashed_password.strip() == "":
        return True
    if username != settings.security.username:
        return False

    return verify_password(password, hashed_password)


def create_token(data: dict, ttl: timedelta) -> str:
    """Creates an access token string.

    Args:
        data: Data to be encoded.
        ttl: Minutes after which the token is expired.

    Returns:
        The access token string.
    """

    to_encode = data.copy()
    exp = datetime.now(timezone.utc) + ttl

    to_encode.update({"exp": exp})
    encoded_token = jwt.encode(
        to_encode, settings.security.token_secret, algorithm="HS256"
    )

    return encoded_token


async def is_authorized(token: Annotated[str, Depends(oauth2_scheme)]):
    """Checks whether user successfully logged in or not and hence is authorized or not.

    Args:
        token: The access token provided using `Authorization` header.

    Raises:
        HTTPException: In case token is invalid or expired.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.security.token_secret, algorithms=["HS256"]
        )
        username = payload.get("sub")

        if username != settings.security.username:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception
