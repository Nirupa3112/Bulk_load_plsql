from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import (
    initialize_database,
    pool,
)
from app.routes.constituents import router


@asynccontextmanager
async def lifespan(app: FastAPI):

    pool.open(wait=True)

    initialize_database()

    yield

    pool.close()


app = FastAPI(
    title="BITA Index Constituents API",
    description=(
        "Append-only ingestion and historical "
        "index constituent API."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(
    router,
    prefix="/api/v1",
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }