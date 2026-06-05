from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
PROCESSED_ROOT = PROJECT_ROOT / "data" / "processed" / "langgraph"
IGNORED_COMPANY_WORDS = {"inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "ltd", "ltd.", "llc", "plc", "group", "holdings", "ag", "sa", "nv", "the"}
COMPANY_ALIASES = {
    "google": ["google", "alphabet", "google llc"],
    "alphabet": ["alphabet", "google", "google llc"],
    "meta": ["meta", "facebook", "instagram", "whatsapp", "meta platforms"],
    "facebook": ["facebook", "meta", "meta platforms", "instagram", "whatsapp"],
    "amazon": ["amazon", "aws", "amazon web services"],
    "amazon web services": ["amazon", "aws", "amazon web services"],
    "microsoft": ["microsoft"],
    "tesla": ["tesla"],
}


def company_to_slug(company_name: str) -> str:
    slug = str(company_name).strip().lower().replace("&", "and")
    slug = "".join(ch if ch.isalnum() else "_" for ch in slug)
    slug = "_".join(part for part in slug.split("_") if part)
    return slug or "company"


def company_aliases(company_name: str) -> list[str]:
    normalized = " ".join(str(company_name).strip().lower().replace("&", " and ").replace("-", " ").split())
    aliases = COMPANY_ALIASES.get(normalized, [normalized])
    seen: set[str] = set()
    results: list[str] = []
    for alias in aliases + [normalized]:
        cleaned = " ".join(str(alias).strip().lower().split())
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            results.append(cleaned)
    return results


def company_keywords(company_name: str) -> list[str]:
    keywords: list[str] = []
    seen: set[str] = set()
    for alias in company_aliases(company_name):
        for part in alias.split():
            if len(part) < 3 or part in IGNORED_COMPANY_WORDS:
                continue
            if part not in seen:
                seen.add(part)
                keywords.append(part)
    return keywords


def raw_dir_for_company(company_name: str) -> Path:
    return RAW_ROOT / company_to_slug(company_name)


def artifact_root_for_company(company_name: str) -> Path:
    return PROCESSED_ROOT / company_to_slug(company_name)
