from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class SearchQueryType(str, Enum):
    DIRECT = "direct"
    VERIFICATION = "verification"
    CONTROVERSY = "controversy"
    TEMPORAL = "temporal"
    REGULATORY = "regulatory"
    OTHER = "other"


class SearchQuery(BaseModel):
    query_id: str = Field(..., description="Unique identifier for the query.")
    claim_id: str = Field(..., description="Identifier of the claim this query belongs to.")
    query_text: str = Field(..., description="Search query text.")
    query_type: SearchQueryType = Field(default=SearchQueryType.OTHER)
    rationale: str = Field(..., description="Short explanation of why this query was generated.")


class SearchResult(BaseModel):
    result_id: str = Field(..., description="Unique identifier for the search result.")
    query_id: str = Field(..., description="Identifier of the originating query.")
    claim_id: str = Field(..., description="Identifier of the related claim.")
    url: HttpUrl
    title: str = Field(..., description="Result title.")
    snippet: str = Field(default="", description="Snippet returned by the search provider.")
    source_name: str = Field(..., description="Detected source or domain label.")
    rank: int = Field(..., ge=1, description="Rank returned by the search provider.")
    published_at: str | None = Field(default=None, description="Publication date if available.")
