from __future__ import annotations

from pydantic import BaseModel, Field


class Settings(BaseModel):
    llm_model_name: str = Field(default="")
    search_backend: str = Field(default="duckduckgo")
    max_queries_per_claim: int = Field(default=3, ge=1)
    max_results_per_query: int = Field(default=5, ge=1)
