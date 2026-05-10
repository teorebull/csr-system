from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .claim import ClaimCandidate
from .evidence import EvidenceDocument, EvidenceSnippet
from .query import SearchQuery, SearchResult
from .report import FinalReport


class DocumentRecord(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the source document.")
    company: str = Field(..., description="Company the document belongs to.")
    path: str = Field(..., description="Local path or external location.")
    title: str = Field(..., description="Human-readable document title.")
    raw_text: str = Field(default="", description="Full extracted text.")
    page_count: int | None = Field(default=None, ge=1)


class RunLogEntry(BaseModel):
    node_name: str = Field(..., description="Graph node that produced the event.")
    status: str = Field(..., description="Event status such as started, completed, or failed.")
    message: str = Field(..., description="Short log message.")


class PipelineState(BaseModel):
    user_query: str = Field(..., description="Natural language request provided by the user.")
    company_name: str = Field(..., description="Target company for the analysis.")
    document_paths: list[str] = Field(default_factory=list)
    max_pages_per_document: int = Field(default=0, ge=0)
    max_page_chars: int = Field(default=0, ge=0)
    documents: list[DocumentRecord] = Field(default_factory=list)
    pages: list[dict[str, Any]] = Field(default_factory=list)
    claims: list[dict[str, Any]] = Field(default_factory=list)
    future_claims: list[dict[str, Any]] = Field(default_factory=list)
    claims_candidates: list[dict[str, Any]] = Field(default_factory=list)
    normalized_claims: list[dict[str, Any]] = Field(default_factory=list)
    queries: list[dict[str, Any]] = Field(default_factory=list)
    search_queries: list[dict[str, Any]] = Field(default_factory=list)
    search_results: list[dict[str, Any]] = Field(default_factory=list)
    vector_chunks: list[dict[str, Any]] = Field(default_factory=list)
    evidence_documents: list[EvidenceDocument] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    ranked_evidence: list[dict[str, Any]] = Field(default_factory=list)
    claim_assessments: list[dict[str, Any]] = Field(default_factory=list)
    final_report: dict[str, Any] | None = Field(default=None)
    logs: list[RunLogEntry] = Field(default_factory=list)
