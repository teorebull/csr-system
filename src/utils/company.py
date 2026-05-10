from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed" / "langgraph"


def company_to_slug(company_name: str) -> str:
    slug = str(company_name).strip().lower().replace("&", "and")
    slug = "".join(ch if ch.isalnum() else "_" for ch in slug)
    slug = "_".join(part for part in slug.split("_") if part)
    return slug or "microsoft"


def raw_dir_for_company(company_name: str) -> Path:
    return RAW_ROOT / company_to_slug(company_name)


def artifact_root_for_company(company_name: str) -> Path:
    return PROCESSED_ROOT / company_to_slug(company_name)
