from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from matcher import exact_search
from schemas import SearchRequest, SearchResponse

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_lyrics(
    payload: SearchRequest, db: Session = Depends(get_db)
) -> SearchResponse:
    results = exact_search(db, payload.query, limit=payload.limit)
    return SearchResponse(
        query=payload.query,
        total_results=len(results),
        results=results,
        message=None if results else "No matches found.",
    )