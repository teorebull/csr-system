from __future__ import annotations

from pydantic import BaseModel, Field

from .claim import Claim, ClaimCandidate
from .evidence import EvidenceDocument, EvidenceSnippet
from .query import SearchQuery, SearchResult
from .report import ClaimAssessment, FinalReport


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
    documents: list[DocumentRecord] = Field(default_factory=list)
    claims_candidates: list[ClaimCandidate] = Field(default_factory=list)
    normalized_claims: list[Claim] = Field(default_factory=list)
    search_queries: list[SearchQuery] = Field(default_factory=list)
    search_results: list[SearchResult] = Field(default_factory=list)
    evidence_documents: list[EvidenceDocument] = Field(default_factory=list)
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    claim_assessments: list[ClaimAssessment] = Field(default_factory=list)
    final_report: FinalReport | None = Field(default=None)
    logs: list[RunLogEntry] = Field(default_factory=list)
