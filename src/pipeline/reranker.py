from __future__ import annotations

import csv
import math
import re
from pathlib import Path

try:
    import torch
    import transformers.utils.import_utils as transformers_import_utils

    transformers_import_utils._librosa_available = False
    from transformers import AutoModel, AutoTokenizer
except ImportError:
    torch = None
    AutoModel = None
    AutoTokenizer = None

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

from src.utils.company import COMPANY_ALIASES, company_aliases, company_keywords


MIN_TEXT_LENGTH = 80
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
MAX_EMBEDDING_TEXT_LENGTH = 1200

GREENWASHING_TERMS = {
    "ai", "cloud", "datacenter", "data", "center", "centers", "scope", "emissions",
    "carbon", "greenwashing", "criticism", "controversy", "methodology", "assurance",
    "offset", "offsets", "renewable", "certificates", "recs", "location", "market",
    "supply", "chain", "increase", "growth", "rising", "water", "waste",
}

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "their", "this", "to",
    "was", "were", "will", "with", "our", "we", "they", "them", "than", "into", "about",
    "across", "all", "also", "can", "do", "does", "not", "per", "year", "years",
}


def load_csv_rows(csv_path: Path) -> list[dict]:
    """Load CSV rows used for reranking evidence."""

    rows = []
    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)
    return rows


def build_claim_lookup(claims: list[dict]) -> dict:
    """Index claims by normalized claim id."""

    return {claim["normalized_claim_id"]: claim for claim in claims}


def normalize_text(text: str) -> str:
    """Normalize text for token overlap scoring."""

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> set[str]:
    """Split text into the tokens used for heuristic scoring."""

    normalized = normalize_text(text)
    tokens = set()
    for word in normalized.split():
        if len(word) < 3 or word in STOPWORDS:
            continue
        tokens.add(word)
    return tokens


def overlap_score(claim_text: str, evidence_text: str) -> float:
    """Measure how much evidence text overlaps the claim text."""

    claim_tokens = tokenize(claim_text)
    evidence_tokens = tokenize(evidence_text)
    if not claim_tokens or not evidence_tokens:
        return 0.0
    return len(claim_tokens.intersection(evidence_tokens)) / len(claim_tokens)


def rank_bonus(result_rank: str) -> float:
    """Reward evidence that surfaced early in search results."""

    try:
        rank = int(result_rank)
    except ValueError:
        return 0.0
    return {1: 0.15, 2: 0.10, 3: 0.05}.get(rank, 0.0)


def query_type_bonus(query_type: str) -> float:
    """Add a small bonus for more useful query types."""

    return {"verification": 0.08, "contradiction": 0.10, "criticism": 0.10, "methodology": 0.07, "context": 0.06}.get(query_type, 0.0)


def source_quality_bonus(source_quality_score: str) -> float:
    """Convert a source-quality score into a reranking bonus."""

    try:
        return float(source_quality_score) * 0.12
    except ValueError:
        return 0.0


def greenwashing_signal_score(evidence: dict) -> float:
    """Reward evidence that touches the project's greenwashing themes."""

    text = f"{evidence.get('title', '')} {evidence.get('snippet', '')} {evidence.get('query_text', '')}"
    matched_terms = tokenize(text).intersection(GREENWASHING_TERMS)
    return min(len(matched_terms) * 0.02, 0.12)


def combined_evidence_text(evidence: dict) -> str:
    """Build the text blob used by the reranker heuristics."""

    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    query_text = evidence.get("query_text", "")
    extracted_text = evidence.get("extracted_text", "")
    return f"{title} {snippet} {query_text} {extracted_text}".lower()


def claim_company_keywords(claim: dict) -> list[str]:
    """Infer company-specific keywords from the claim itself."""

    sources = [
        str(claim.get("claim_text", "")),
        str(claim.get("document_name", "")),
        str(claim.get("source_excerpts", "")),
    ]
    text = " ".join(sources).lower()
    for canonical_name, aliases in COMPANY_ALIASES.items():
        if any(alias in text for alias in aliases + company_aliases(canonical_name)):
            return company_keywords(canonical_name)
    return []


def extract_fiscal_year_terms(text: str) -> set[str]:
    """Extract year tokens that matter for claim-specific matching."""

    terms = set()
    for match in re.findall(r"\bfy\s?(\d{2})\b", text.lower()):
        terms.add(f"fy{match}")
        terms.add(f"20{match}")
    for match in re.findall(r"\b20\d{2}\b", text.lower()):
        terms.add(match)
    return terms


def extract_percentages(text: str) -> set[str]:
    """Pull percentage strings from text for exact matching."""

    return set(re.findall(r"\b\d+(?:\.\d+)?\s?%", text.lower()))


def text_contains_any(text: str, terms: set[str]) -> bool:
    """Check whether any exact term appears in the text."""

    for term in terms:
        pattern = rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])"
        if re.search(pattern, text):
            return True
    return False


def matched_terms(text: str, terms: set[str]) -> set[str]:
    """Return the subset of terms that appear in the text."""

    matches = set()
    for term in terms:
        pattern = rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])"
        if re.search(pattern, text):
            matches.add(term)
    return matches


def check_required_term_group(claim_text: str, evidence_text: str, terms: set[str], label: str) -> tuple[float, str | None]:
    """Score whether a required topic group is present in the evidence."""

    if not text_contains_any(claim_text, terms):
        return 0.0, None
    if text_contains_any(evidence_text, terms):
        return 0.05, f"matched_{label}"
    return -0.05, f"missing_{label}"


def check_exclusive_topic_terms(claim_text: str, evidence_text: str, terms: set[str], label: str) -> tuple[float, str | None]:
    """Score whether a claim-specific topic term is preserved in evidence."""

    claim_terms = matched_terms(claim_text, terms)
    if not claim_terms:
        return 0.0, None
    evidence_terms = matched_terms(evidence_text, terms)
    if claim_terms.intersection(evidence_terms):
        return 0.07, f"matched_{label}"
    if evidence_terms:
        return -0.08, f"mismatched_{label}"
    return -0.04, f"missing_{label}"


def compute_specificity(claim: dict, evidence: dict) -> tuple[float, str]:
    """Estimate how specifically the evidence matches the claim."""

    claim_text = claim.get("claim_text", "").lower()
    evidence_text = combined_evidence_text(evidence)
    adjustment = 0.0
    notes = []

    if claim.get("claim_family", "other") in {"environmental", "governance_ai"}:
        company_terms = claim_company_keywords(claim)
        if company_terms and any(term in evidence_text for term in company_terms):
            adjustment += 0.03
            notes.append("matched_company")
        elif company_terms:
            adjustment -= 0.08
            notes.append("missing_company")

    claim_years = extract_fiscal_year_terms(claim_text)
    if claim_years:
        if any(year in evidence_text for year in claim_years):
            adjustment += 0.05
            notes.append("matched_year")
        else:
            adjustment -= 0.04
            notes.append("missing_year")

    claim_percentages = extract_percentages(claim_text)
    if claim_percentages:
        evidence_percentages = extract_percentages(evidence_text)
        if claim_percentages.intersection(evidence_percentages):
            adjustment += 0.07
            notes.append("matched_exact_percentage")
        elif evidence_percentages:
            adjustment += 0.02
            notes.append("matched_percentage_context")
        else:
            adjustment -= 0.04
            notes.append("missing_percentage")

    is_water_claim = text_contains_any(claim_text, {"water", "withdrawal", "withdrawals", "discharge", "discharges"}) or "water consumption" in claim_text
    if is_water_claim:
        water_delta, water_note = check_exclusive_topic_terms(claim_text, evidence_text, {"withdrawal", "withdrawals", "consumption", "discharge", "discharges"}, "water_metric")
        adjustment += water_delta
        if water_note:
            notes.append(water_note)

    scope_delta, scope_note = check_exclusive_topic_terms(claim_text, evidence_text, {"scope 1", "scope 2", "scope 3"}, "scope")
    adjustment += scope_delta
    if scope_note:
        notes.append(scope_note)

    term_groups = [
        ({"market-based", "market based"}, "market_based"),
        ({"location-based", "location based"}, "location_based"),
        ({"recs", "renewable energy certificate", "renewable energy certificates", "eac", "eacs"}, "certificate_accounting"),
        ({"ppa", "ppas", "power purchase agreement", "power purchase agreements"}, "ppa"),
        ({"supplier", "suppliers", "supply chain"}, "supplier"),
        ({"spend", "spend-based", "spend based", "emissions factor", "emission factor", "primary data"}, "supplier_methodology"),
        ({"carbon removal", "carbon removals", "carbon credit", "carbon credits", "offset", "offsets"}, "carbon_credit"),
        ({"carbon neutral", "carbon neutrality", "carbon negative"}, "carbon_commitment"),
    ]

    for terms, label in term_groups:
        delta, note = check_required_term_group(claim_text, evidence_text, terms, label)
        adjustment += delta
        if note:
            notes.append(note)

    if any(term in claim_text for term in {"human rights", "labor", "diversity", "inclusion", "belonging"}):
        if any(term in evidence_text for term in {"human rights", "labor", "diversity", "inclusion", "belonging", "workforce", "employee"}):
            adjustment += 0.06
            notes.append("matched_social_csr")
        else:
            adjustment -= 0.05
            notes.append("missing_social_csr")

    score = max(0.0, min(1.0, 0.5 + adjustment))
    if not notes:
        notes.append("no_specificity_signals")
    return round(score, 4), "; ".join(notes)


def build_evidence_text_for_embedding(evidence: dict) -> str:
    text = f"{evidence.get('title', '')}. {evidence.get('snippet', '')}. {evidence.get('extracted_text', '')}".strip()
    text = re.sub(r"\s+", " ", text)
    return text[:MAX_EMBEDDING_TEXT_LENGTH]


def load_embedding_model():
    if AutoTokenizer is None or AutoModel is None or torch is None:
        return None
    try:
        tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
        model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)
        model.eval()
        return {"tokenizer": tokenizer, "model": model}
    except Exception:
        return None


def load_cross_encoder():
    if CrossEncoder is None:
        return None
    try:
        return CrossEncoder(RERANKER_MODEL_NAME)
    except Exception:
        return None


def mean_pool_embedding(model_bundle: dict, text: str):
    tokenizer = model_bundle["tokenizer"]
    model = model_bundle["model"]
    encoded = tokenizer(text, padding=True, truncation=True, max_length=256, return_tensors="pt")
    with torch.no_grad():
        output = model(**encoded)
    token_embeddings = output.last_hidden_state
    attention_mask = encoded["attention_mask"].unsqueeze(-1).expand(token_embeddings.size()).float()
    summed = torch.sum(token_embeddings * attention_mask, dim=1)
    counts = torch.clamp(attention_mask.sum(dim=1), min=1e-9)
    embedding = summed / counts
    embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
    return embedding[0]


def cosine_similarity(vector_a, vector_b) -> float:
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for value_a, value_b in zip(vector_a, vector_b):
        value_a = float(value_a)
        value_b = float(value_b)
        dot_product += value_a * value_b
        norm_a += value_a * value_a
        norm_b += value_b * value_b
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))))


def compute_semantic_similarity(model, claim: dict, evidence: dict) -> float:
    if model is None:
        return 0.0
    claim_text = claim.get("claim_text", "")
    evidence_text = build_evidence_text_for_embedding(evidence)
    if not claim_text or not evidence_text:
        return 0.0
    try:
        claim_embedding = mean_pool_embedding(model, claim_text)
        evidence_embedding = mean_pool_embedding(model, evidence_text)
    except Exception:
        return 0.0
    return round(cosine_similarity(claim_embedding, evidence_embedding), 4)


def compute_cross_encoder_score(model, claim: dict, evidence: dict) -> float:
    if model is None:
        return 0.0
    claim_text = claim.get("claim_text", "")
    evidence_text = build_evidence_text_for_embedding(evidence)
    if not claim_text or not evidence_text:
        return 0.0
    try:
        score = model.predict([(claim_text, evidence_text)], convert_to_numpy=True)
        raw_score = float(score[0])
        return max(0.0, min(1.0, 1.0 / (1.0 + math.exp(-raw_score))))
    except Exception:
        return 0.0


def compute_relevance_score(claim: dict, evidence: dict, semantic_similarity: float, specificity_score: float) -> float:
    claim_text = claim["claim_text"]
    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    extracted_text = evidence.get("extracted_text", "")

    score = 0.0
    score += semantic_similarity * 0.45
    score += overlap_score(claim_text, title) * 0.25
    score += overlap_score(claim_text, snippet) * 0.25
    score += overlap_score(claim_text, extracted_text) * 0.25
    score += rank_bonus(evidence.get("result_rank", ""))
    score += query_type_bonus(evidence.get("query_type", ""))
    score += source_quality_bonus(evidence.get("source_quality_score", "0"))
    score += greenwashing_signal_score(evidence)
    score += (specificity_score - 0.5) * 0.35
    return round(score, 4)


def diversify_ranked_rows(rows: list[dict]) -> list[dict]:
    sorted_rows = sorted(rows, key=lambda row: row["relevance_score"], reverse=True)
    selected_rows = []
    used_query_types = set()
    used_urls = set()

    for row in sorted_rows:
        query_type = row.get("query_type", "")
        url = row.get("url", "")
        source_label = row.get("source_quality_label", "unknown")
        if query_type in used_query_types or url in used_urls:
            continue
        if source_label == "low":
            continue
        selected_rows.append(row)
        used_query_types.add(query_type)
        used_urls.add(url)

    for row in sorted_rows:
        url = row.get("url", "")
        source_label = row.get("source_quality_label", "unknown")
        if row in selected_rows or url in used_urls:
            continue
        if source_label == "low":
            continue
        selected_rows.append(row)
        used_urls.add(url)

    for row in sorted_rows:
        if row not in selected_rows:
            selected_rows.append(row)
    return selected_rows


def filter_usable_evidence(claim_lookup: dict, evidence_rows: list[dict]) -> list[dict]:
    usable_rows = []
    for row in evidence_rows:
        success = str(row.get("extraction_success", "")).strip().lower() == "true"
        extracted_text = row.get("extracted_text", "").strip()
        source_quality_label = str(row.get("source_quality_label", "unknown")).strip().lower()
        claim = claim_lookup.get(row.get("normalized_claim_id", ""), {})
        claim_text = str(claim.get("claim_text", row.get("claim_text", "")))

        if not success or len(extracted_text) < MIN_TEXT_LENGTH:
            continue
        if source_quality_label == "low":
            continue
        if claim_text and overlap_score(claim_text, f"{row.get('title', '')} {row.get('snippet', '')} {extracted_text}") < 0.10:
            continue
        usable_rows.append(row)
    return usable_rows


def rerank_evidence(claim_lookup: dict, evidence_rows: list[dict]) -> list[dict]:
    grouped_rows = {}
    embedding_model = load_embedding_model()
    cross_encoder = load_cross_encoder()

    for evidence in evidence_rows:
        claim_id = evidence["normalized_claim_id"]
        if claim_id not in claim_lookup:
            continue
        claim = claim_lookup[claim_id]
        semantic_similarity = compute_semantic_similarity(embedding_model, claim, evidence)
        cross_encoder_score = compute_cross_encoder_score(cross_encoder, claim, evidence)
        specificity_score, specificity_notes = compute_specificity(claim, evidence)
        relevance_score = compute_relevance_score(claim, evidence, semantic_similarity, specificity_score)
        relevance_score += cross_encoder_score * 0.35

        ranked_row = {
            "normalized_claim_id": claim_id,
            "claim_text": claim["claim_text"],
            "query_type": evidence["query_type"],
            "query_text": evidence["query_text"],
            "result_rank": evidence["result_rank"],
            "title": evidence["title"],
            "url": evidence["url"],
            "source": evidence["source"],
            "source_quality_score": evidence.get("source_quality_score", "0"),
            "source_quality_label": evidence.get("source_quality_label", "unknown"),
            "snippet": evidence["snippet"],
            "content_type": evidence["content_type"],
            "semantic_similarity_score": semantic_similarity,
            "cross_encoder_score": cross_encoder_score,
            "specificity_score": specificity_score,
            "specificity_notes": specificity_notes,
            "final_rerank_score": relevance_score,
            "relevance_score": relevance_score,
            "extraction_notes": evidence["extraction_notes"],
            "extracted_text": evidence["extracted_text"],
        }

        grouped_rows.setdefault(claim_id, []).append(ranked_row)

    all_ranked_rows = []
    for rows in grouped_rows.values():
        sorted_rows = diversify_ranked_rows(rows)
        for index, row in enumerate(sorted_rows, start=1):
            row["evidence_rank"] = index
            all_ranked_rows.append(row)
    return all_ranked_rows


def should_accept_evidence_row(row: dict) -> bool:
    if not row.get("extraction_notes"):
        return False
    if str(row.get("source_quality_label", "unknown")).strip().lower() == "low":
        return False
    if str(row.get("title", "")).strip() == "" and str(row.get("snippet", "")).strip() == "":
        return False
    return True


def save_ranked_evidence(rows: list[dict], output_path: Path) -> None:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id", "claim_text", "query_type", "query_text", "result_rank", "title", "url",
                "source", "source_quality_score", "source_quality_label", "snippet", "content_type",
                "semantic_similarity_score", "cross_encoder_score", "specificity_score", "specificity_notes", "final_rerank_score",
                "relevance_score", "evidence_rank", "extraction_notes", "extracted_text",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
