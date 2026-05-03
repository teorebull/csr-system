import csv
csv.field_size_limit(10**7)
import math
import re
from pathlib import Path

try:
    import torch
    import transformers.utils.import_utils as transformers_import_utils

    # Avoid optional audio dependencies when loading text-only embedding models.
    transformers_import_utils._librosa_available = False

    from transformers import AutoModel, AutoTokenizer
except ImportError:
    torch = None
    AutoModel = None
    AutoTokenizer = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLAIMS_CSV = PROJECT_ROOT / "data" / "processed" / "agent_3" / "prioritized_claims.csv"
EVIDENCE_CSV = PROJECT_ROOT / "data" / "processed" / "agent_6" / "evidence_candidates.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_7" / "ranked_evidence.csv"
MIN_TEXT_LENGTH = 80
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_EMBEDDING_TEXT_LENGTH = 1200

GREENWASHING_TERMS = {
    "ai", "cloud", "datacenter", "data", "center", "centers", "scope", "emissions",
    "carbon", "greenwashing", "criticism", "controversy", "methodology", "assurance",
    "offset", "offsets", "renewable", "certificates", "recs", "location", "market",
    "supply", "chain", "increase", "growth", "rising", "water", "waste"
}


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "their", "this", "to",
    "was", "were", "will", "with", "our", "we", "they", "them", "than", "into", "about",
    "across", "all", "also", "can", "do", "does", "not", "per", "year", "years"
}


def load_csv_rows(csv_path: Path) -> list[dict]:
    """Load rows from a CSV file."""
    rows = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(row)

    return rows


def build_claim_lookup(claims: list[dict]) -> dict:
    """Map normalized claim ids to claim rows."""
    lookup = {}

    for claim in claims:
        lookup[claim["normalized_claim_id"]] = claim

    return lookup


def normalize_text(text: str) -> str:
    """Create a simple normalized text form for matching."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> set[str]:
    """Convert text into a simple keyword set."""
    normalized = normalize_text(text)
    words = normalized.split()
    tokens = set()

    for word in words:
        if len(word) < 3:
            continue

        if word in STOPWORDS:
            continue

        tokens.add(word)

    return tokens


def overlap_score(claim_text: str, evidence_text: str) -> float:
    """Measure simple token overlap between claim and evidence."""
    claim_tokens = tokenize(claim_text)
    evidence_tokens = tokenize(evidence_text)

    if not claim_tokens or not evidence_tokens:
        return 0.0

    overlap = claim_tokens.intersection(evidence_tokens)
    return len(overlap) / len(claim_tokens)


def rank_bonus(result_rank: str) -> float:
    """Small bonus for higher search ranks."""
    try:
        rank = int(result_rank)
    except ValueError:
        return 0.0

    if rank == 1:
        return 0.15
    if rank == 2:
        return 0.10
    if rank == 3:
        return 0.05
    return 0.0


def query_type_bonus(query_type: str) -> float:
    """Give a small bonus depending on the search intention."""
    if query_type == "verification":
        return 0.08
    if query_type == "contradiction":
        return 0.10
    if query_type == "criticism":
        return 0.10
    if query_type == "methodology":
        return 0.07
    if query_type == "context":
        return 0.06
    return 0.0


def source_quality_bonus(source_quality_score: str) -> float:
    """Convert Agent 5 source-quality score into a small reranking signal."""
    try:
        quality_score = float(source_quality_score)
    except ValueError:
        quality_score = 0.0

    return quality_score * 0.12


def greenwashing_signal_score(evidence: dict) -> float:
    """Reward evidence that contains useful greenwashing-risk context."""
    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    query_text = evidence.get("query_text", "")
    text = f"{title} {snippet} {query_text}"
    tokens = tokenize(text)

    if not tokens:
        return 0.0

    matched_terms = tokens.intersection(GREENWASHING_TERMS)
    return min(len(matched_terms) * 0.02, 0.12)


def combined_evidence_text(evidence: dict) -> str:
    """Join searchable evidence fields for specificity checks."""
    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    query_text = evidence.get("query_text", "")
    extracted_text = evidence.get("extracted_text", "")
    return f"{title} {snippet} {query_text} {extracted_text}".lower()


def extract_fiscal_year_terms(text: str) -> set[str]:
    """Extract FY-style years and likely calendar-year equivalents."""
    terms = set()

    for match in re.findall(r"\bfy\s?(\d{2})\b", text.lower()):
        terms.add(f"fy{match}")
        terms.add(f"20{match}")

    for match in re.findall(r"\b20\d{2}\b", text.lower()):
        terms.add(match)

    return terms


def extract_percentages(text: str) -> set[str]:
    """Extract percentage values from text."""
    return set(re.findall(r"\b\d+(?:\.\d+)?\s?%", text.lower()))


def text_contains_any(text: str, terms: set[str]) -> bool:
    """Check whether any term appears as a phrase in text."""
    for term in terms:
        normalized_term = re.escape(term.lower())
        pattern = rf"(?<![a-z0-9]){normalized_term}(?![a-z0-9])"

        if re.search(pattern, text):
            return True

    return False


def matched_terms(text: str, terms: set[str]) -> set[str]:
    """Return phrase-level matches without substring false positives."""
    matches = set()

    for term in terms:
        normalized_term = re.escape(term.lower())
        pattern = rf"(?<![a-z0-9]){normalized_term}(?![a-z0-9])"

        if re.search(pattern, text):
            matches.add(term)

    return matches


def check_required_term_group(claim_text: str, evidence_text: str, terms: set[str], label: str) -> tuple[float, str | None]:
    """Reward matching a specific claim term group and penalize missing it."""
    claim_has_term = text_contains_any(claim_text, terms)

    if not claim_has_term:
        return 0.0, None

    if text_contains_any(evidence_text, terms):
        return 0.05, f"matched_{label}"

    return -0.05, f"missing_{label}"


def check_exclusive_topic_terms(claim_text: str, evidence_text: str, terms: set[str], label: str) -> tuple[float, str | None]:
    """Penalize evidence that discusses sibling metrics but misses the exact one."""
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
    """Score whether evidence matches claim-specific facts beyond broad semantics."""
    claim_text = claim.get("claim_text", "").lower()
    evidence_text = combined_evidence_text(evidence)
    adjustment = 0.0
    notes = []

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

    is_water_claim = text_contains_any(claim_text, {"water", "withdrawal", "withdrawals", "discharge", "discharges"})
    is_water_claim = is_water_claim or "water consumption" in claim_text

    if is_water_claim:
        water_delta, water_note = check_exclusive_topic_terms(
            claim_text,
            evidence_text,
            {"withdrawal", "withdrawals", "consumption", "discharge", "discharges"},
            "water_metric",
        )
        adjustment += water_delta
        if water_note:
            notes.append(water_note)

    scope_delta, scope_note = check_exclusive_topic_terms(
        claim_text,
        evidence_text,
        {"scope 1", "scope 2", "scope 3"},
        "scope",
    )
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

    score = max(0.0, min(1.0, 0.5 + adjustment))

    if not notes:
        notes.append("no_specificity_signals")

    return round(score, 4), "; ".join(notes)


def build_evidence_text_for_embedding(evidence: dict) -> str:
    """Create compact evidence text for semantic similarity."""
    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    extracted_text = evidence.get("extracted_text", "")
    text = f"{title}. {snippet}. {extracted_text}".strip()
    text = re.sub(r"\s+", " ", text)
    return text[:MAX_EMBEDDING_TEXT_LENGTH]


def load_embedding_model():
    """Load a transformer embedding model if dependencies are available."""
    if AutoTokenizer is None or AutoModel is None or torch is None:
        print("transformers/torch are not installed; using rule-based reranking only.")
        return None

    try:
        print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
        model = AutoModel.from_pretrained(EMBEDDING_MODEL_NAME)
        model.eval()
        return {"tokenizer": tokenizer, "model": model}
    except Exception as error:
        print(f"Could not load embedding model, using rule-based reranking only: {error}")
        return None


def mean_pool_embedding(model_bundle: dict, text: str):
    """Create one normalized mean-pooled embedding with transformers."""
    tokenizer = model_bundle["tokenizer"]
    model = model_bundle["model"]

    encoded = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

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
    """Compute cosine similarity for two embedding vectors."""
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

    similarity = dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))
    return max(0.0, min(1.0, similarity))


def compute_semantic_similarity(model, claim: dict, evidence: dict) -> float:
    """Use embeddings to estimate semantic claim-evidence relevance."""
    if model is None:
        return 0.0

    claim_text = claim.get("claim_text", "")
    evidence_text = build_evidence_text_for_embedding(evidence)

    if not claim_text or not evidence_text:
        return 0.0

    try:
        claim_embedding = mean_pool_embedding(model, claim_text)
        evidence_embedding = mean_pool_embedding(model, evidence_text)
    except Exception as error:
        print(f"Embedding similarity failed for {claim.get('normalized_claim_id', '')}: {error}")
        return 0.0

    return round(cosine_similarity(claim_embedding, evidence_embedding), 4)


def compute_relevance_score(claim: dict, evidence: dict, semantic_similarity: float, specificity_score: float) -> float:
    """Compute a simple reranking score for one claim-evidence pair."""
    claim_text = claim["claim_text"]
    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    extracted_text = evidence.get("extracted_text", "")

    title_score = overlap_score(claim_text, title)
    snippet_score = overlap_score(claim_text, snippet)
    text_score = overlap_score(claim_text, extracted_text)

    score = 0.0
    score += semantic_similarity * 0.45
    score += title_score * 0.25
    score += snippet_score * 0.25
    score += text_score * 0.25
    score += rank_bonus(evidence.get("result_rank", ""))
    score += query_type_bonus(evidence.get("query_type", ""))
    score += source_quality_bonus(evidence.get("source_quality_score", "0"))
    score += greenwashing_signal_score(evidence)
    # Keep specificity as a diagnostic signal for now. In validation it was useful
    # to inspect, but too brittle to improve the final ranking consistently.
    score += (specificity_score - 0.5) * 0.0

    return round(score, 4)


def diversify_ranked_rows(rows: list[dict]) -> list[dict]:
    """Keep top ranks useful for LLM reasoning by mixing query intentions."""
    sorted_rows = sorted(rows, key=lambda row: row["relevance_score"], reverse=True)
    selected_rows = []
    used_query_types = set()
    used_urls = set()

    for row in sorted_rows:
        query_type = row.get("query_type", "")
        url = row.get("url", "")

        if query_type in used_query_types:
            continue

        if url in used_urls:
            continue

        selected_rows.append(row)
        used_query_types.add(query_type)
        used_urls.add(url)

    for row in sorted_rows:
        url = row.get("url", "")

        if row in selected_rows:
            continue

        if url in used_urls:
            continue

        selected_rows.append(row)
        used_urls.add(url)

    for row in sorted_rows:
        if row in selected_rows:
            continue

        selected_rows.append(row)

    return selected_rows


def filter_usable_evidence(evidence_rows: list[dict]) -> list[dict]:
    """Keep only evidence rows that extracted some usable text."""
    usable_rows = []

    for row in evidence_rows:
        success = str(row.get("extraction_success", "")).strip().lower() == "true"
        extracted_text = row.get("extracted_text", "").strip()

        if not success:
            continue

        if len(extracted_text) < MIN_TEXT_LENGTH:
            continue

        usable_rows.append(row)

    return usable_rows


def rerank_evidence(claim_lookup: dict, evidence_rows: list[dict]) -> list[dict]:
    """Score and rank evidence per normalized claim."""
    grouped_rows = {}
    embedding_model = load_embedding_model()

    for evidence in evidence_rows:
        claim_id = evidence["normalized_claim_id"]

        if claim_id not in claim_lookup:
            continue

        claim = claim_lookup[claim_id]
        semantic_similarity = compute_semantic_similarity(embedding_model, claim, evidence)
        specificity_score, specificity_notes = compute_specificity(claim, evidence)
        relevance_score = compute_relevance_score(claim, evidence, semantic_similarity, specificity_score)

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
            "specificity_score": specificity_score,
            "specificity_notes": specificity_notes,
            "final_rerank_score": relevance_score,
            "relevance_score": relevance_score,
            "extraction_notes": evidence["extraction_notes"],
            "extracted_text": evidence["extracted_text"],
        }

        if claim_id not in grouped_rows:
            grouped_rows[claim_id] = []

        grouped_rows[claim_id].append(ranked_row)

    all_ranked_rows = []

    for claim_id, rows in grouped_rows.items():
        sorted_rows = diversify_ranked_rows(rows)

        for index, row in enumerate(sorted_rows, start=1):
            row["evidence_rank"] = index
            all_ranked_rows.append(row)

    return all_ranked_rows


def save_ranked_evidence(rows: list[dict], output_path: Path) -> None:
    """Save reranked evidence rows to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "claim_text",
                "query_type",
                "query_text",
                "result_rank",
                "title",
                "url",
                "source",
                "source_quality_score",
                "source_quality_label",
                "snippet",
                "content_type",
                "semantic_similarity_score",
                "specificity_score",
                "specificity_notes",
                "final_rerank_score",
                "relevance_score",
                "evidence_rank",
                "extraction_notes",
                "extracted_text",
            ],
        )
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def main() -> None:
    if not CLAIMS_CSV.exists():
        print(f"Claims CSV not found: {CLAIMS_CSV}")
        return

    if not EVIDENCE_CSV.exists():
        print(f"Evidence CSV not found: {EVIDENCE_CSV}")
        return

    print("Loading normalized claims...")
    claims = load_csv_rows(CLAIMS_CSV)
    claim_lookup = build_claim_lookup(claims)

    print("Loading evidence candidates...")
    evidence_rows = load_csv_rows(EVIDENCE_CSV)
    evidence_rows = filter_usable_evidence(evidence_rows)

    print("Reranking evidence...")
    ranked_rows = rerank_evidence(claim_lookup, evidence_rows)

    save_ranked_evidence(ranked_rows, OUTPUT_CSV)

    print(f"Usable evidence rows: {len(evidence_rows)}")
    print(f"Ranked evidence rows: {len(ranked_rows)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
