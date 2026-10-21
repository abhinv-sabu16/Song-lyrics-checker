from fastapi import APIRouter

from schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_lyrics(payload: SearchRequest) -> SearchResponse:
    # Stub: Day 4 replaces this with a real database search.
    return SearchResponse(
        query=payload.query,
        total_results=0,
        results=[],
        message="No matches found.",
    )