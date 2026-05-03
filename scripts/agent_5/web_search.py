import csv
from pathlib import Path
from urllib.parse import urlparse

from ddgs import DDGS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_4" / "queries.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "agent_5" / "search_results.csv"
MAX_RESULTS = 8
COMPANY_NAME = "Microsoft" # Later we will use this as teh company variabel used by user
EXTRA_EXCLUDED_DOMAINS = [
    "youtube.com",
    "youtu.be",
    "linkedin.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
    "news.ycombinator.com",
]

HIGH_QUALITY_DOMAINS = {
    "npr.org",
    "wired.com",
    "theverge.com",
    "trellis.net",
    "theregister.com",
    "businessgreen.com",
    "reuters.com",
    "apnews.com",
    "carbonbrief.org",
    "iea.org",
    "sec.gov",
    "cdp.net",
    "ghgprotocol.org",
    "theconversation.com",
    "stand.earth",
    "computerweekly.com",
    "datacenterdynamics.com",
    "grist.org",
    "greenbiz.com",
    "esgdive.com",
    "policyreview.info",
    "enabledemissions.com",
    "theguardian.com",
    "cleantechnica.com",
    "renewableenergyworld.com",
}

LOW_QUALITY_DOMAIN_HINTS = {
    "windowsforum.com",
    "websitehostingreview.org",
    "bot.to",
    "tipranks.com",
    "allaboutai.com",
    "hashlytics.io",
    "poniaktimes.com",
    "richardhartley.com",
    "the-14.com",
}


def normalize_company_name(company_name: str) -> list[str]:
    """Create simple company keywords for filtering."""
    company_name = company_name.lower().strip()
    company_name = company_name.replace("&", " and ")
    company_name = company_name.replace("-", " ")
    parts = company_name.split()

    ignored_words = {
        "inc",
        "inc.",
        "corp",
        "corp.",
        "corporation",
        "company",
        "co",
        "co.",
        "ltd",
        "ltd.",
        "llc",
        "plc",
        "group",
        "holdings",
        "ag",
        "sa",
        "nv",
        "the",
    }

    keywords = []

    for part in parts:
        part = part.strip()

        if not part or part in ignored_words:
            continue

        if len(part) >= 3:
            keywords.append(part)

    return keywords


def get_domain(url: str) -> str:
    """Extract the domain from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def score_source_quality(url: str) -> tuple[float, str]:
    """Give a simple source-quality signal for later reranking."""
    domain = get_domain(url).removeprefix("www.")

    if not domain:
        return 0.0, "unknown"

    if domain in HIGH_QUALITY_DOMAINS:
        return 1.0, "high"

    for weak_hint in LOW_QUALITY_DOMAIN_HINTS:
        if weak_hint in domain:
            return -0.5, "low"

    if domain.endswith(".gov") or domain.endswith(".edu"):
        return 1.0, "high"

    if domain.endswith(".org"):
        return 0.5, "medium"

    return 0.0, "unknown"


def is_company_owned_domain(url: str, company_keywords: list[str]) -> bool:
    """Check whether the URL looks company-owned.

    This is heuristic but useful for the MVP.
    """
    domain = get_domain(url)

    if not domain:
        return False

    for excluded_domain in EXTRA_EXCLUDED_DOMAINS:
        excluded_domain = excluded_domain.lower().strip()

        if excluded_domain and excluded_domain in domain:
            return True

    for keyword in company_keywords:
        if keyword in domain:
            return True

    return False


def mentions_company(result: dict, company_keywords: list[str]) -> bool:
    """Keep only external results that still mention the company."""
    title = result.get("title", "").lower()
    snippet = result.get("body", "").lower()
    url = result.get("href", "").lower()
    combined_text = f"{title} {snippet} {url}"

    if "microsoft word" in title and "microsoft" not in snippet and "microsoft" not in url:
        return False

    for keyword in company_keywords:
        if keyword in combined_text:
            return True

    return False


def filter_external_results(results: list[dict], company_name: str) -> list[dict]:
    """Remove company-owned sources and keep externally relevant ones."""
    company_keywords = normalize_company_name(company_name)
    filtered_results = []

    for result in results:
        url = result.get("href", "")

        if is_company_owned_domain(url, company_keywords):
            continue

        if not mentions_company(result, company_keywords):
            continue

        filtered_results.append(result)

    return filtered_results


def load_queries(csv_path: Path) -> list[dict]:
    """Load generated queries from Agent 4."""
    queries = []

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            queries.append(row)

    return queries


def search_query(query: dict, ddgs_client: DDGS) -> list[dict]:
    """Run one web search query and return structured results."""
    query_text = query["query_text"].strip()

    if not query_text:
        return []

    try:
        results = ddgs_client.text(query_text, max_results=MAX_RESULTS)
    except Exception as error:
        print(f"Search failed for query '{query_text}': {error}")
        return []

    results = filter_external_results(results, COMPANY_NAME)

    formatted_results = []

    for index, result in enumerate(results, start=1):
        source_quality_score, source_quality_label = score_source_quality(result.get("href", ""))

        formatted_results.append(
            {
                "normalized_claim_id": query["normalized_claim_id"],
                "query_type": query["query_type"],
                "query_text": query_text,
                "result_rank": index,
                "title": result.get("title", ""),
                "url": result.get("href", ""),
                "snippet": result.get("body", ""),
                "source": result.get("source", ""),
                "source_quality_score": source_quality_score,
                "source_quality_label": source_quality_label,
            }
        )

    return formatted_results


def search_all_queries(queries: list[dict]) -> list[dict]:
    """Run all web searches and collect the results."""
    all_results = []
    ddgs_client = DDGS()

    for query in queries:
        claim_id = query["normalized_claim_id"]
        query_type = query["query_type"]
        print(f"Searching {query_type} for {claim_id}...")

        query_results = search_query(query, ddgs_client)

        for result in query_results:
            all_results.append(result)

    return all_results


def save_results_csv(results: list[dict], output_path: Path) -> None:
    """Save search results to CSV."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "normalized_claim_id",
                "query_type",
                "query_text",
                "result_rank",
                "title",
                "url",
                "snippet",
                "source",
                "source_quality_score",
                "source_quality_label",
            ],
        )
        writer.writeheader()

        for result in results:
            writer.writerow(result)


def main() -> None:
    if not INPUT_CSV.exists():
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    print("Loading queries...")
    queries = load_queries(INPUT_CSV)

    print(f"Company filter: {COMPANY_NAME}")
    print("Running web search...")
    results = search_all_queries(queries)

    save_results_csv(results, OUTPUT_CSV)

    print(f"Search results collected: {len(results)}")
    print(f"Saved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
