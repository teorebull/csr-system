"""Typed schemas for pipeline inputs, outputs, and shared state."""

from .claim import Claim, ClaimCandidate, ClaimGroup, ClaimPriority, ClaimType, ClaimTopic
from .evidence import EvidenceDocument, EvidenceSnippet, EvidenceSourceType
from .query import SearchQuery, SearchQueryType, SearchResult
from .report import ClaimAssessment, FinalReport, GreenwashingRiskLevel, SupportLabel
from .state import DocumentRecord, PipelineState, RunLogEntry

__all__ = [
    "Claim",
    "ClaimAssessment",
    "ClaimCandidate",
    "ClaimGroup",
    "ClaimPriority",
    "ClaimTopic",
    "ClaimType",
    "DocumentRecord",
    "EvidenceDocument",
    "EvidenceSnippet",
    "EvidenceSourceType",
    "FinalReport",
    "GreenwashingRiskLevel",
    "PipelineState",
    "RunLogEntry",
    "SearchQuery",
    "SearchQueryType",
    "SearchResult",
    "SupportLabel",
]
