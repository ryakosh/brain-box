from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles as FastAPIStaticFiles

from brain_box.router import api_router
from brain_box.db import create_db_and_tables

BASE_DIR = Path(__file__).parent.parent.resolve()
FRONTEND_DIR = BASE_DIR / "webapp"


class StaticFiles(FastAPIStaticFiles):
    async def get_response(self, path: str, scope):
        resp = await super().get_response(path, scope)

        if resp.status_code == 404 and Path(path).suffix == "":
            return await super().get_response(f"{path}.html", scope)
        else:
            return resp


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()

    yield


app = FastAPI(
    title="Brain Box API",
    version="0.1.0",
    lifespan=lifespan,
)


app.include_router(api_router, prefix="/api")
app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="webapp",
)
