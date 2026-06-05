from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """High-level type of extracted CSR claim."""

    PERFORMANCE = "performance"
    COMMITMENT = "commitment"
    POLICY = "policy"
    RECOGNITION = "recognition"
    OTHER = "other"


class ClaimTopic(str, Enum):
    """Topic bucket used to organize claims."""

    EMISSIONS = "emissions"
    ENERGY = "energy"
    CLIMATE = "climate"
    SUPPLY_CHAIN = "supply_chain"
    LABOR = "labor"
    HUMAN_RIGHTS = "human_rights"
    ETHICS = "ethics"
    GOVERNANCE = "governance"
    BIODIVERSITY = "biodiversity"
    WASTE = "waste"
    WATER = "water"
    OTHER = "other"


class ClaimPriority(str, Enum):
    """Priority assigned to a claim after scoring."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClaimCandidate(BaseModel):
    """Raw claim candidate extracted from a source document."""

    claim_id: str = Field(..., description="Unique identifier for the extracted claim.")
    company: str = Field(..., description="Company the claim refers to.")
    claim_text: str = Field(..., description="Claim as extracted from the source document.")
    source_document: str = Field(..., description="Document name or identifier.")
    source_page: int | None = Field(default=None, ge=1)
    source_excerpt: str = Field(..., description="Supporting excerpt from the source document.")
    claim_type: ClaimType = Field(default=ClaimType.OTHER)
    topic: ClaimTopic = Field(default=ClaimTopic.OTHER)
    time_reference: str | None = Field(default=None, description="Year or period mentioned by the claim.")
    priority: ClaimPriority = Field(default=ClaimPriority.MEDIUM)


class Claim(ClaimCandidate):
    """Normalized claim ready for downstream analysis."""

    canonical_text: str = Field(..., description="Normalized version of the claim.")
    normalized_from_ids: list[str] = Field(
        default_factory=list,
        description="Source claim candidate identifiers merged into this normalized claim.",
    )


class ClaimGroup(BaseModel):
    """Group of claims merged into one canonical claim."""

    canonical_claim_id: str = Field(..., description="Identifier of the canonical normalized claim.")
    member_claim_ids: list[str] = Field(default_factory=list)
    merge_reason: str = Field(..., description="Short explanation of why the claims were grouped.")
