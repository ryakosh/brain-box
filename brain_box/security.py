from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from brain_box import utils
from brain_box.config import settings


password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/refresh-token")


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


def create_token(
    sub: str,
    token_type: Literal["access", "refresh"],
    ttl: timedelta,
    jti: UUID | None = None,
) -> str:
    """Creates a token string.

    Args:
        sub: Subject of the token.
        token_type: Whether this is a `refresh` or `access` token.
        ttl: Minutes after which the token is expired.
        jti: The token ID.

    Returns:
        The token string.
    """

    to_encode = {
        "sub": sub,
        "token_type": token_type,
        "exp": datetime.now(timezone.utc) + ttl,
        "iat": utils.now(),
    }

    if jti:
        to_encode["jti"] = str(jti)

    encoded_token = jwt.encode(
        to_encode, settings.security.token_secret, algorithm="HS256"
    )

    return encoded_token


async def is_authorized(access_token: Annotated[str, Depends(oauth2_scheme)]):
    """Checks whether user successfully logged in or not and hence is authorized or not.

    Args:
        access_token: The access token provided using `Authorization` header.

    Raises:
        HTTPException: In case access token is invalid or expired.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            access_token, settings.security.token_secret, algorithms=["HS256"]
        )

        token_type = payload.get("token_type")
        sub = payload.get("sub")

        if token_type != "access" or sub != settings.security.username:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception
