from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SupportLabel(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


class GreenwashingRiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ClaimAssessment(BaseModel):
    claim_id: str = Field(..., description="Identifier of the evaluated claim.")
    final_stance: SupportLabel
    justification: str = Field(..., description="Structured textual justification for the final stance.")
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    greenwashing_signal: bool = Field(default=False)
    notes: str | None = Field(default=None)


class FinalReport(BaseModel):
    company: str = Field(..., description="Company evaluated by the pipeline.")
    total_claims: int = Field(..., ge=0)
    supported: int = Field(default=0, ge=0)
    partially_supported: int = Field(default=0, ge=0)
    unsupported: int = Field(default=0, ge=0)
    contradicted: int = Field(default=0, ge=0)
    credibility_score: float = Field(..., ge=-0.5, le=1.0)
    greenwashing_risk_level: GreenwashingRiskLevel
    final_conclusion: str = Field(..., description="Final narrative conclusion for the company.")
    claim_assessments: list[ClaimAssessment] = Field(default_factory=list)
