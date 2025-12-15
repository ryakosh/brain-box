from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

import brain_box.crud.auth as crud_auth
from brain_box.config import settings
from brain_box.db import get_session
from brain_box.models.auth import AccessTokenRead, RefreshTokenCreate
from brain_box.security import create_token, verify_user


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/refresh-token")
async def refresh_token(
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

    jti = uuid4()
    ttl = timedelta(minutes=settings.security.refresh_token_ttl)

    crud_auth.create_refresh_token(
        db,
        RefreshTokenCreate(
            id=jti,
            expires_at=datetime.now(timezone.utc) + ttl,
        ),
    )
    refresh_token = create_token(
        sub=form_data.username, token_type="refresh", ttl=ttl, jti=jti
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=True,
        max_age=settings.security.refresh_token_ttl * 60,
    )

    return {}


@auth_router.post("/access-token", response_model=AccessTokenRead)
async def access_token(request: Request):
    """Generates an access token for the user."""

    invalid_refresh_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
    )

    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise invalid_refresh_token_exception

    try:
        payload = jwt.decode(
            refresh_token_cookie, settings.security.token_secret, algorithms=["HS256"]
        )

        token_type = payload.get("token_type")
        sub = payload.get("sub")

        if token_type != "refresh" and sub != settings.security.username:
            raise invalid_refresh_token_exception

        ttl = timedelta(minutes=settings.security.access_token_ttl)
        token = create_token(sub=sub, token_type="access", ttl=ttl)

        return AccessTokenRead(token=token, token_type="bearer")

    except jwt.InvalidTokenError:
        raise invalid_refresh_token_exception
