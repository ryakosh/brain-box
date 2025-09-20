from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from brain_box.router import api_router
from brain_box.db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    create_db_and_tables()

    yield


app = FastAPI(
    title="Brain Box API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router)
