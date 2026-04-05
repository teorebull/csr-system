from __future__ import annotations

from src.schemas.evidence import EvidenceSourceType


DOMAIN_TYPE_HINTS = {
    ".gov": EvidenceSourceType.REGULATOR,
    ".edu": EvidenceSourceType.ACADEMIC,
    ".org": EvidenceSourceType.NGO,
}


def infer_source_type(domain: str) -> EvidenceSourceType:
    for suffix, source_type in DOMAIN_TYPE_HINTS.items():
        if domain.endswith(suffix):
            return source_type
    return EvidenceSourceType.OTHER
