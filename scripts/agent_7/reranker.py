import csv
import re
from pathlib import Path


CLAIMS_CSV = "data/processed/agent_3/normalized_claims.csv"
EVIDENCE_CSV = "data/processed/agent_6/evidence_candidates.csv"
OUTPUT_CSV = "data/processed/agent_7/ranked_evidence.csv"
MIN_TEXT_LENGTH = 80


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "its", "of", "on", "or", "that", "the", "their", "this", "to",
    "was", "were", "will", "with", "our", "we", "they", "them", "than", "into", "about",
    "across", "all", "also", "can", "do", "does", "not", "per", "year", "years"
}


def load_csv_rows(csv_path: str) -> list[dict]:
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
    if query_type == "core":
        return 0.05
    if query_type == "critical":
        return 0.03
    return 0.0


def compute_relevance_score(claim: dict, evidence: dict) -> float:
    """Compute a simple reranking score for one claim-evidence pair."""
    claim_text = claim["claim_text"]
    title = evidence.get("title", "")
    snippet = evidence.get("snippet", "")
    extracted_text = evidence.get("extracted_text", "")

    title_score = overlap_score(claim_text, title)
    snippet_score = overlap_score(claim_text, snippet)
    text_score = overlap_score(claim_text, extracted_text)

    score = 0.0
    score += title_score * 0.25
    score += snippet_score * 0.25
    score += text_score * 0.45
    score += rank_bonus(evidence.get("result_rank", ""))
    score += query_type_bonus(evidence.get("query_type", ""))

    return round(score, 4)


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

    for evidence in evidence_rows:
        claim_id = evidence["normalized_claim_id"]

        if claim_id not in claim_lookup:
            continue

        claim = claim_lookup[claim_id]
        relevance_score = compute_relevance_score(claim, evidence)

        ranked_row = {
            "normalized_claim_id": claim_id,
            "claim_text": claim["claim_text"],
            "query_type": evidence["query_type"],
            "query_text": evidence["query_text"],
            "result_rank": evidence["result_rank"],
            "title": evidence["title"],
            "url": evidence["url"],
            "source": evidence["source"],
            "snippet": evidence["snippet"],
            "content_type": evidence["content_type"],
            "relevance_score": relevance_score,
            "extraction_notes": evidence["extraction_notes"],
            "extracted_text": evidence["extracted_text"],
        }

        if claim_id not in grouped_rows:
            grouped_rows[claim_id] = []

        grouped_rows[claim_id].append(ranked_row)

    all_ranked_rows = []

    for claim_id, rows in grouped_rows.items():
        sorted_rows = sorted(rows, key=lambda row: row["relevance_score"], reverse=True)

        for index, row in enumerate(sorted_rows, start=1):
            row["evidence_rank"] = index
            all_ranked_rows.append(row)

    return all_ranked_rows


def save_ranked_evidence(rows: list[dict], output_path: str) -> None:
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
                "snippet",
                "content_type",
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
    if not Path(CLAIMS_CSV).exists():
        print(f"Claims CSV not found: {CLAIMS_CSV}")
        return

    if not Path(EVIDENCE_CSV).exists():
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
