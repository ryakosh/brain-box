from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from brain_box.config import settings
from brain_box.security import Token, create_token, verify_user


auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/token")
async def token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Generates an access token for the user."""

    verified = verify_user(form_data.username, form_data.password)

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    ttl = timedelta(minutes=settings.security.token_ttl)
    token = create_token(data={"sub": "admin"}, ttl=ttl)

    return Token(token=token, token_type="bearer")
