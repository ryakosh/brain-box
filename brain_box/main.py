from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Response
from fastapi.staticfiles import StaticFiles as FastAPIStaticFiles
from starlette.exceptions import HTTPException

from brain_box.db import create_db_and_tables, engine
from brain_box.routers.topics import topics_router
from brain_box.routers.entries import entries_router
from brain_box.routers.auth import auth_router
from brain_box.security import is_authorized
from brain_box.config import settings

BASE_DIR = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = BASE_DIR / "brain_box" / "webapp"


class StaticFiles(FastAPIStaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                return await super().get_response("index.html", scope)
            else:
                raise ex


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables(engine)

    yield


app = FastAPI(
    title="Brain Box API",
    version="0.1.0",
    lifespan=lifespan,
)
router_deps = []

if settings.security.hashed_password:
    router_deps.append(Depends(is_authorized))

api_router = APIRouter(prefix="/api")
api_router.include_router(topics_router, dependencies=router_deps)
api_router.include_router(entries_router, dependencies=router_deps)
api_router.include_router(auth_router)


@app.head("/health")
async def health_check():
    """
    Health check endpoint, returns 200 OK if the server is healthy.
    """

    return Response(status_code=200)


app.include_router(api_router)

if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="webapp",
    )
