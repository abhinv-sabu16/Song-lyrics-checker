from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers.search import router as search_router
from schemas import HealthResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # creates tables if they don't exist yet
    yield


app = FastAPI(title="Song Lyric Checker API", version="0.4.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(search_router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")