from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.search import router as search_router
from schemas import HealthResponse

app = FastAPI(title="Song Lyric Checker API", version="0.2.0")

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