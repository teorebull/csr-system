from __future__ import annotations

from pydantic import BaseModel, Field

from src.schemas.report import SupportLabel


class GoldClaimLabel(BaseModel):
    claim_id: str = Field(...)
    expected_label: SupportLabel
    notes: str | None = Field(default=None)
