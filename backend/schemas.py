from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MatchType(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"


class SearchRequest(BaseModel):
    """Body of POST /api/search."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    query: str = Field(
        min_length=1,
        max_length=200,
        description="Lyric phrase to search for. Whitespace is trimmed.",
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results returned.")
    min_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum text similarity (0-100). If omitted, the server default is used.",
    )


class MatchResult(BaseModel):
    """One ranked candidate. Never contains full lyrics, only a short excerpt."""

    song_id: int
    title: str
    artist: str
    matched_excerpt: str = Field(max_length=300)
    similarity_score: float = Field(
        ge=0,
        le=100,
        description="Text similarity between the query and the matched line. "
        "This is NOT a probability that the song is correct.",
    )
    match_type: MatchType
    start_time: float | None = Field(
        default=None, ge=0, description="Seconds into the audio clip (audio search only)."
    )
    end_time: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_time_order(self):
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time < self.start_time
        ):
            raise ValueError("end_time must not be earlier than start_time")
        return self


class SearchResponse(BaseModel):
    query: str
    total_results: int = Field(ge=0)
    results: list[MatchResult]
    message: str | None = Field(
        default=None, description="Human-readable note, e.g. 'No matches found.'"
    )


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None