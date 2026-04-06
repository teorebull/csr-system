import csv
import re
from difflib import SequenceMatcher
from pathlib import Path


INPUT_CSV = "data/processed/agent_2/claims.csv"
NORMALIZED_OUTPUT_CSV = "data/processed/agent_3/normalized_claims.csv"
FUTURE_OUTPUT_CSV = "data/processed/agent_3/future_claims.csv"
SIMILARITY_THRESHOLD = 0.88


def load_claims(csv_path: str) -> list[dict]:
    """Load extracted claims from Agent 2."""
    claims = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            claims.append(row)

    return claims


def normalize_text(text: str) -> str:
    """Create a simple normalized version of a claim for matching."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[“”\"'`´]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def are_similar_claims(claim_a: dict, claim_b: dict) -> bool:
    """Check whether two claims are similar enough to merge."""
    if claim_a["topic"] != claim_b["topic"]:
        return False

    if claim_a["claim_type"] != claim_b["claim_type"]:
        return False

    text_a = normalize_text(claim_a["claim_text"])
    text_b = normalize_text(claim_b["claim_text"])

    similarity = SequenceMatcher(None, text_a, text_b).ratio()
    return similarity >= SIMILARITY_THRESHOLD


def split_future_claims(claims: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separate future claims from the rest."""
    current_claims = []
    future_claims = []

    for claim in claims:
        is_future = str(claim["is_future"]).strip().lower() == "true"

        if is_future:
            future_claims.append(claim)
        else:
            current_claims.append(claim)

    return current_claims, future_claims


def merge_claim_group(group: list[dict], normalized_id: int) -> dict:
    """Create one normalized row from a group of similar claims."""
    first_claim = group[0]

    original_ids = []
    page_numbers = []
    excerpts = []

    for claim in group:
        original_ids.append(claim["claim_id"])
        page_numbers.append(str(claim["page_number"]))
        excerpts.append(claim["source_excerpt"])

    unique_page_numbers = sorted(set(page_numbers), key=lambda x: int(x))
    unique_excerpts = []

    for excerpt in excerpts:
        if excerpt not in unique_excerpts:
            unique_excerpts.append(excerpt)

    return {
        "normalized_claim_id": f"normalized_claim_{normalized_id}",
        "document_name": first_claim["document_name"],
        "claim_text": first_claim["claim_text"],
        "claim_type": first_claim["claim_type"],
        "topic": first_claim["topic"],
        "original_claim_ids": "; ".join(original_ids),
        "page_numbers": "; ".join(unique_page_numbers),
        "source_excerpts": " || ".join(unique_excerpts),
        "group_size": len(group),
    }


def normalize_claims(claims: list[dict]) -> list[dict]:
    """Merge obvious duplicate or near-duplicate claims."""
    normalized_claims = []
    used_indices = set()
    normalized_id = 1

    for index, claim in enumerate(claims):
        if index in used_indices:
            continue

        group = [claim]
        used_indices.add(index)

        for other_index in range(index + 1, len(claims)):
            if other_index in used_indices:
                continue

            other_claim = claims[other_index]

            if are_similar_claims(claim, other_claim):
                group.append(other_claim)
                used_indices.add(other_index)

        normalized_claim = merge_claim_group(group, normalized_id)
        normalized_claims.append(normalized_claim)
        normalized_id += 1

    return normalized_claims


def save_csv(rows: list[dict], output_path: str, fieldnames: list[str]) -> None:
    """Save rows to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def main() -> None:
    if not Path(INPUT_CSV).exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading claims...")
    claims = load_claims(INPUT_CSV)

    print("Separating future claims...")
    current_claims, future_claims = split_future_claims(claims)

    print("Normalizing current claims...")
    normalized_claims = normalize_claims(current_claims)

    save_csv(
        normalized_claims,
        NORMALIZED_OUTPUT_CSV,
        [
            "normalized_claim_id",
            "document_name",
            "claim_text",
            "claim_type",
            "topic",
            "original_claim_ids",
            "page_numbers",
            "source_excerpts",
            "group_size",
        ],
    )

    save_csv(
        future_claims,
        FUTURE_OUTPUT_CSV,
        [
            "claim_id",
            "document_name",
            "page_number",
            "claim_text",
            "claim_type",
            "is_verifiable",
            "claim_quality_score",
            "is_reporting_claim",
            "topic",
            "is_future",
            "source_excerpt",
        ],
    )

    print(f"Current claims loaded: {len(current_claims)}")
    print(f"Future claims separated: {len(future_claims)}")
    print(f"Normalized claims saved: {len(normalized_claims)}")
    print(f"Saved normalized claims to: {NORMALIZED_OUTPUT_CSV}")
    print(f"Saved future claims to: {FUTURE_OUTPUT_CSV}")


if __name__ == "__main__":
    main()
