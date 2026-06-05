from __future__ import annotations

import argparse
import csv
import os
import time
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from src.graph.nodes import (
    run_claim_extractor,
    run_claim_normalizer,
    run_document_loader,
    run_evidence_analyzer,
    run_evidence_fetcher,
    run_judge,
    run_query_generator,
    run_reranker,
    run_web_search,
)
from src.pipeline.judge_aggregator import load_csv_rows
from src.schemas.state import PipelineState
from src.utils.company import artifact_root_for_company, raw_dir_for_company


PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

NODE_SEQUENCE = [
    ("load_documents", run_document_loader),
    ("extract_claims", run_claim_extractor),
    ("normalize_claims", run_claim_normalizer),
    ("generate_queries", run_query_generator),
    ("search_evidence", run_web_search),
    ("fetch_evidence", run_evidence_fetcher),
    ("rerank_evidence", run_reranker),
    ("analyze_claims", run_evidence_analyzer),
    ("aggregate_report", run_judge),
]

NODE_NAMES = [name for name, _ in NODE_SEQUENCE]
def log_node(name: str, node_fn):
    def wrapped(state):
        start = time.perf_counter()
        print(f"[{name}] start", flush=True)
        result = node_fn(state)
        elapsed = time.perf_counter() - start
        print(f"[{name}] done in {elapsed:.2f}s", flush=True)
        return result

    return wrapped


def company_to_slug(company_name: str) -> str:
    slug = company_name.strip().lower().replace("&", "and")
    slug = "".join(ch if ch.isalnum() else "_" for ch in slug)
    slug = "_".join(part for part in slug.split("_") if part)
    return slug or "microsoft"


def resolve_raw_dir(company_name: str) -> Path:
    company_dir = raw_dir_for_company(company_name)
    if company_dir.exists():
        return company_dir
    return RAW_DIR


def resolve_artifact_dir(company_name: str) -> Path:
    return artifact_root_for_company(company_name)


def find_pdf_paths(raw_dir: Path) -> list[str]:
    pdfs = sorted(raw_dir.glob("*.pdf")) + sorted(raw_dir.glob("*.PDF"))
    unique_paths = []
    seen = set()

    for pdf in pdfs:
        resolved = str(pdf.resolve()).lower()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_paths.append(str(pdf))

    return unique_paths


def build_state(
    company_name: str,
    user_query: str,
    document_paths: list[str],
    max_pages_per_document: int,
    max_page_chars: int,
) -> PipelineState:
    return PipelineState(
        user_query=user_query,
        company_name=company_name,
        document_paths=document_paths,
        max_pages_per_document=max_pages_per_document,
        max_page_chars=max_page_chars,
    )


def filter_environmental_claims(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if str(row.get("claim_family", "")).strip().lower() in {"environmental", "governance_ai", "other"}
    ]


def load_resume_state(start_at: str, company_name: str, user_query: str) -> PipelineState:
    artifact_dir = resolve_artifact_dir(company_name)
    # Resume runs rebuild only the pieces that downstream nodes depend on.
    state = PipelineState(
        user_query=user_query,
        company_name=company_name,
        document_paths=[],
        max_pages_per_document=0,
        max_page_chars=0,
    )

    load_state_rows(state, artifact_dir, start_at)

    return state


def load_rows(artifact_dir: Path, agent: str, filename: str) -> list[dict]:
    """Load a CSV artifact from one of the saved agent folders."""

    return load_csv_rows(artifact_dir / agent / filename)


def load_state_rows(state: PipelineState, artifact_dir: Path, start_at: str) -> None:
    """Populate a resume state with the artifacts needed by later nodes."""

    if start_at == "normalize_claims":
        extracted_claims = load_rows(artifact_dir, "agent_2", "claims.csv")
        state.claims_candidates = extracted_claims
        state.claims = extracted_claims

    if start_at in {"generate_queries", "search_evidence", "fetch_evidence", "rerank_evidence", "analyze_claims", "aggregate_report"}:
        prioritized_claims = load_rows(artifact_dir, "agent_3", "prioritized_claims.csv")
        state.claims = filter_environmental_claims(prioritized_claims)
        state.normalized_claims = prioritized_claims

    if start_at in {"search_evidence", "fetch_evidence", "rerank_evidence", "analyze_claims", "aggregate_report"}:
        queries = load_rows(artifact_dir, "agent_4", "queries.csv")
        state.queries = queries
        state.search_queries = queries

    if start_at in {"fetch_evidence", "rerank_evidence", "analyze_claims", "aggregate_report"}:
        state.search_results = load_rows(artifact_dir, "agent_5", "search_results.csv")

    if start_at in {"rerank_evidence", "analyze_claims", "aggregate_report"}:
        state.ranked_evidence = load_rows(artifact_dir, "agent_6", "evidence_candidates.csv")

    if start_at in {"analyze_claims", "aggregate_report"}:
        state.ranked_evidence = load_rows(artifact_dir, "agent_7", "ranked_evidence.csv")

    if start_at == "aggregate_report":
        state.claim_assessments = load_rows(artifact_dir, "agent_8", "claim_assessments.csv")


def cap_pages_in_state(state: PipelineState, max_pages_per_document: int) -> PipelineState:
    if max_pages_per_document <= 0 or not state.pages:
        return state

    limited_pages = []
    counts: dict[str, int] = {}

    for page in state.pages:
        document_id = page.get("document_id", "unknown")
        counts[document_id] = counts.get(document_id, 0) + 1
        if counts[document_id] <= max_pages_per_document:
            limited_pages.append(page)

    state.pages = limited_pages
    return state


def build_workflow(start_at: str, stop_at: str):
    # The graph is rebuilt on each run so start/stop points stay flexible.
    graph = StateGraph(PipelineState)

    for node_name, node_fn in NODE_SEQUENCE:
        graph.add_node(node_name, log_node(node_name, node_fn))

    start_index = NODE_NAMES.index(start_at)
    stop_index = NODE_NAMES.index(stop_at)

    if stop_index < start_index:
        raise ValueError(f"stop_at must come after start_at: {start_at} -> {stop_at}")

    graph.add_edge(START, NODE_NAMES[start_index])

    for index in range(start_index, stop_index):
        graph.add_edge(NODE_NAMES[index], NODE_NAMES[index + 1])

    graph.add_edge(NODE_NAMES[stop_index], END)

    return graph.compile()


def main() -> None:
    run_start = time.perf_counter()
    parser = argparse.ArgumentParser(description="Run the CSR LangGraph workflow.")
    parser.add_argument("--company", default="Microsoft", help="Company name to analyze.")
    parser.add_argument(
        "--query",
        default="Analyze the company's sustainability claims for greenwashing risk.",
        help="Natural language request for the run state.",
    )
    parser.add_argument(
        "--document",
        action="append",
        dest="documents",
        default=[],
        help="Explicit document path to analyze. Can be repeated.",
    )
    parser.add_argument(
        "--mode",
        default=os.environ.get("PIPELINE_MODE", "normal"),
        choices=["fast", "normal", "strict", "thorough"],
        help="Pipeline mode passed through to downstream nodes.",
    )
    parser.add_argument(
        "--start-at",
        default="load_documents",
        choices=NODE_NAMES,
        help="Start the LangGraph workflow from this node.",
    )
    parser.add_argument(
        "--stop-at",
        default=None,
        choices=NODE_NAMES,
        help="Stop the LangGraph workflow after this node for a quick validation run.",
    )
    parser.add_argument(
        "--max-documents",
        type=int,
        default=1,
        help="Limit the number of documents used for validation runs.",
    )
    parser.add_argument(
        "--max-pages-per-document",
        type=int,
        default=1,
        help="Limit the number of pages loaded per document for validation runs.",
    )
    parser.add_argument(
        "--max-page-chars",
        type=int,
        default=2000,
        help="Limit the amount of text sent from each page to the extractor.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass claim extraction and assessment caches for a fresh run.",
    )
    args = parser.parse_args()

    os.environ["PIPELINE_MODE"] = args.mode
    os.environ["PIPELINE_DISABLE_CACHE"] = "1" if args.no_cache else "0"

    stop_at = args.stop_at or ("load_documents" if args.mode == "fast" else "aggregate_report")
    start_at = args.start_at

    if start_at == "load_documents":
        raw_dir = resolve_raw_dir(args.company)
        document_paths = args.documents or find_pdf_paths(raw_dir)
        if args.max_documents > 0:
            document_paths = document_paths[: args.max_documents]
        if not document_paths:
            print(f"No PDF files found in: {raw_dir}")
            return

        state = build_state(
            args.company,
            args.query,
            document_paths,
            args.max_pages_per_document,
            args.max_page_chars,
        )
    else:
        state = load_resume_state(start_at, args.company, args.query)

    workflow = build_workflow(start_at, stop_at)
    result = workflow.invoke(state)
    total_elapsed = time.perf_counter() - run_start

    if isinstance(result, dict):
        final_report = result.get("final_report", {})
    else:
        final_report = getattr(result, "final_report", {}) or {}

    print(f"Pipeline completed for {args.company}.")
    print(f"Started at: {start_at}")
    print(f"Stopped after: {stop_at}")
    print(f"Elapsed: {total_elapsed:.2f}s")
    if isinstance(final_report, dict):
        print(f"Claims analyzed: {final_report.get('total_claims_analyzed', 0)}")
    print(f"Final summary: {resolve_artifact_dir(args.company) / 'agent_9' / 'final_summary.md'}")


if __name__ == "__main__":
    main()
