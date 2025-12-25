import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from brain_box import utils
import brain_box.crud.auth as crud_auth
from brain_box.config import settings
from brain_box.db import get_session
from brain_box.models.auth import AccessTokenRead, RefreshTokenCreate
from brain_box.security import create_access_token, gen_refresh_token, verify_user


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/login", response_model=AccessTokenRead)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    db: Session = Depends(get_session),
):
    """Generates refresh token for the user."""

    verified = verify_user(form_data.username, form_data.password)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    refresh_token = gen_refresh_token()
    ttl = timedelta(minutes=settings.security.refresh_token_ttl)
    crud_auth.create_refresh_token(
        db,
        RefreshTokenCreate(
            hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + ttl,
        ),
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=settings.security.refresh_token_ttl * 60,
    )

    ttl = timedelta(minutes=settings.security.access_token_ttl)
    token = create_access_token(sub=settings.security.username, ttl=ttl)

    return AccessTokenRead(token=token, token_type="bearer", expires_in=ttl.seconds)


@auth_router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    db: Session = Depends(get_session),
):
    """Logs out the user, removing refresh token cookie."""

    if refresh_token is None:
        return {}

    crud_auth.delete_refresh_token_by_hash(
        db,
        refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=True,
    )

    return {}


@auth_router.post("/token", response_model=AccessTokenRead)
async def token(request: Request, db: Session = Depends(get_session)):
    """Generates an access token for the user."""

    invalid_refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise invalid_refresh_token_exception

    refresh_token_hash = hashlib.sha256(refresh_token_cookie.encode()).hexdigest()
    refresh_token = crud_auth.get_refresh_token_by_hash(
        db, refresh_token_hash=refresh_token_hash
    )

    if refresh_token is None or utils.now() >= refresh_token.expires_at.replace(
        tzinfo=timezone.utc
    ):
        raise invalid_refresh_token_exception

    ttl = timedelta(minutes=settings.security.access_token_ttl)
    token = create_access_token(sub=settings.security.username, ttl=ttl)

    return AccessTokenRead(token=token, token_type="bearer", expires_in=ttl.seconds)
