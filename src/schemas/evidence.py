from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class EvidenceSourceType(str, Enum):
    """Broad source category for an evidence item."""

    REGULATOR = "regulator"
    NGO = "ngo"
    NEWS = "news"
    AUDIT = "audit"
    COMPANY = "company"
    ACADEMIC = "academic"
    DATABASE = "database"
    OTHER = "other"


class EvidenceDocument(BaseModel):
    """Fetched source document used as evidence."""

    evidence_id: str = Field(..., description="Unique identifier for the evidence document.")
    claim_id: str = Field(..., description="Claim the evidence is associated with.")
    url: HttpUrl
    title: str = Field(..., description="Document title.")
    source_name: str = Field(..., description="Source label.")
    source_type: EvidenceSourceType = Field(default=EvidenceSourceType.OTHER)
    publication_date: str | None = Field(default=None)
    extracted_text: str = Field(..., description="Cleaned article or page text.")
    retrieval_notes: str | None = Field(default=None)


class EvidenceSnippet(BaseModel):
    """Relevant excerpt pulled from an evidence document."""

    snippet_id: str = Field(..., description="Unique identifier for the evidence snippet.")
    evidence_id: str = Field(..., description="Parent evidence document identifier.")
    claim_id: str = Field(..., description="Claim the snippet is associated with.")
    text: str = Field(..., description="Relevant excerpt used in the assessment.")
    start_char: int | None = Field(default=None, ge=0)
    end_char: int | None = Field(default=None, ge=0)
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    credibility_score: float | None = Field(default=None, ge=0.0, le=1.0)
    rank: int | None = Field(default=None, ge=1)
