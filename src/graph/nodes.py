from __future__ import annotations

import csv
import json
from pathlib import Path

from src.pipeline.claim_extractor import extract_claims_from_pages
from src.pipeline.claim_normalizer import normalize_claims, prioritize_claims, split_future_claims
from src.pipeline.evidence_analyzer import (
    analyze_all_claims,
    build_claim_lookup,
    group_top_evidence,
    load_assessment_cache,
    save_assessment_cache,
)
from src.pipeline.evidence_fetcher import extract_all_evidence, filter_low_quality_sources, select_best_results
from src.pipeline.document_loader import load_document_pages
from src.pipeline.judge_aggregator import build_final_report, save_final_report_artifacts
from src.pipeline.query_generator import generate_queries_for_all_claims
from src.pipeline.reranker import filter_usable_evidence, rerank_evidence
from src.pipeline.web_search import search_all_queries
from src.pipeline.vector_retrieval import retrieve_chunks_for_claims
from src.schemas.state import DocumentRecord, PipelineState, RunLogEntry
from src.utils.company import artifact_root_for_company


def _filter_environmental_claims(rows: list[dict]) -> list[dict]:
    return [
        row
        for row in rows
        if str(row.get("claim_family", "")).strip().lower() in {"environmental", "governance_ai", "other"}
    ]


def _build_document_id(document_path: str, index: int) -> str:
    safe_stem = Path(document_path).stem.lower().replace(" ", "_")
    return f"doc_{index}_{safe_stem}"


def _company_keywords(company_name: str) -> list[str]:
    ignored_words = {"inc", "inc.", "corp", "corp.", "corporation", "company", "co", "co.", "ltd", "ltd.", "llc", "plc", "group", "holdings", "ag", "sa", "nv", "the"}
    normalized = company_name.lower().replace("&", " and ").replace("-", " ")
    keywords = []
    for part in normalized.split():
        part = part.strip()
        if len(part) >= 3 and part not in ignored_words:
            keywords.append(part)
    return keywords


def _document_matches_company(company_name: str, document_name: str, full_text: str) -> bool:
    haystack = f"{document_name} {full_text[:5000]}".lower()
    keywords = _company_keywords(company_name)
    if not keywords:
        return True
    return any(keyword in haystack for keyword in keywords)


def _save_csv(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _load_json_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json_dict(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def run_document_loader(state: PipelineState) -> PipelineState:
    if not state.document_paths:
        state.logs.append(
            RunLogEntry(
                node_name="document_loader",
                status="skipped",
                message="No document paths were provided.",
            )
        )
        return state

    pages: list[dict] = []
    documents: list[DocumentRecord] = []

    for index, document_path in enumerate(state.document_paths, start=1):
        processed_pages, metadata, _repeated_lines, _low_text_pages, full_text = load_document_pages(document_path)
        document_id = _build_document_id(document_path, index)
        document_name = metadata.get("title") or Path(document_path).stem.replace("-", " ").replace("_", " ").strip()

        if not _document_matches_company(state.company_name, document_name, full_text):
            state.logs.append(
                RunLogEntry(
                    node_name="document_loader",
                    status="skipped",
                    message=f"Skipped document '{document_name}' because it does not appear to match company '{state.company_name}'.",
                )
            )
            continue

        documents.append(
            DocumentRecord(
                document_id=document_id,
                company=state.company_name,
                path=document_path,
                title=document_name,
                raw_text=full_text,
                page_count=metadata.get("page_count"),
            )
        )

        for page in processed_pages:
            pages.append(
                {
                    "document_id": document_id,
                    "document_name": document_name,
                    "document_path": document_path,
                    "page_number": page["page_number"],
                    "text": page["text"],
                }
            )

        if state.max_pages_per_document > 0:
            pages = [
                page
                for page in pages
                if page["document_id"] != document_id
                or page["page_number"] <= state.max_pages_per_document
            ]

    state.documents = documents
    state.pages = pages
    state.logs.append(
        RunLogEntry(
            node_name="document_loader",
            status="completed",
            message=f"Loaded {len(documents)} document(s) and {len(pages)} page(s).",
        )
    )
    return state


def run_claim_normalizer(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    raw_claims = list(state.claims_candidates) if state.claims_candidates else list(state.claims)
    claim_rows = [claim.model_dump() if hasattr(claim, "model_dump") else dict(claim) for claim in raw_claims]

    if not claim_rows:
        state.logs.append(
            RunLogEntry(
                node_name="claim_normalizer",
                status="skipped",
                message="No claims were available for normalization.",
            )
        )
        return state

    current_claims, future_claims = split_future_claims(claim_rows)
    normalized_claims = normalize_claims(current_claims)
    enriched_claims, prioritized_claims, _excluded_claims = prioritize_claims(normalized_claims)
    environmental_prioritized_claims = _filter_environmental_claims(prioritized_claims)

    state.claims = environmental_prioritized_claims
    state.normalized_claims = enriched_claims
    state.future_claims = future_claims
    _save_csv(enriched_claims, artifact_root / "agent_3" / "normalized_claims.csv")
    _save_csv(prioritized_claims, artifact_root / "agent_3" / "prioritized_claims.csv")
    _save_csv(_excluded_claims, artifact_root / "agent_3" / "excluded_claims.csv")
    _save_csv(future_claims, artifact_root / "agent_3" / "future_claims.csv")
    state.logs.append(
        RunLogEntry(
            node_name="claim_normalizer",
            status="completed",
            message=f"Normalized {len(normalized_claims)} claim(s); prioritized {len(prioritized_claims)} total and {len(environmental_prioritized_claims)} environmental claim(s) for downstream analysis.",
        )
    )
    return state


def run_claim_extractor(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    if not state.pages:
        state.logs.append(
            RunLogEntry(
                node_name="claim_extractor",
                status="skipped",
                message="No pages were available for claim extraction.",
            )
        )
        return state

    pages = list(state.pages)
    if state.max_page_chars > 0:
        trimmed_pages = []
        for page in pages:
            text = (page.get("text") or "").strip()
            trimmed_pages.append({**page, "text": text[: state.max_page_chars]})
        pages = trimmed_pages

    disable_cache = str(__import__("os").getenv("PIPELINE_DISABLE_CACHE", "0")).strip() == "1"
    cache_path = artifact_root / "agent_2" / "claim_extraction_cache.json"
    claim_cache = {} if disable_cache else _load_json_dict(cache_path)
    claims, claim_cache, stats = extract_claims_from_pages(pages, claim_cache)
    state.claims_candidates = claims
    state.claims = claims
    _save_csv(claims, artifact_root / "agent_2" / "claims.csv")
    if not disable_cache:
        _save_json_dict(claim_cache, cache_path)
    state.logs.append(
        RunLogEntry(
            node_name="claim_extractor",
            status="completed",
            message=f"Extracted {len(claims)} claim(s); cache hits {stats['cache_hits']}, misses {stats['cache_misses']}.",
        )
    )
    return state


def run_query_generator(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    claim_rows = [claim.model_dump() if hasattr(claim, "model_dump") else dict(claim) for claim in state.claims]

    if not claim_rows:
        state.logs.append(
            RunLogEntry(
                node_name="query_generator",
                status="skipped",
                message="No prioritized claims were available for query generation.",
            )
        )
        return state

    query_rows, _search_queries = generate_queries_for_all_claims(claim_rows)
    state.queries = query_rows
    state.search_queries = query_rows
    _save_csv(query_rows, artifact_root / "agent_4" / "queries.csv")
    message = f"Generated {len(query_rows)} query row(s) from {len(claim_rows)} claim(s)."
    if claim_rows and not query_rows:
        message += " Query generation returned no results; check that Ollama and the Agent 4 model are available."
    state.logs.append(
        RunLogEntry(
            node_name="query_generator",
            status="completed",
            message=message,
        )
    )
    return state


def run_web_search(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    query_rows = [query.model_dump() if hasattr(query, "model_dump") else dict(query) for query in state.search_queries or state.queries]

    if not query_rows:
        state.logs.append(
            RunLogEntry(
                node_name="web_search",
                status="skipped",
                message="No queries were available for web search.",
            )
        )
        return state

    results, _result_models = search_all_queries(query_rows, state.company_name)
    state.search_results = results
    state.ranked_evidence = results
    _save_csv(results, artifact_root / "agent_5" / "search_results.csv")
    state.logs.append(
        RunLogEntry(
            node_name="web_search",
            status="completed",
            message=f"Collected {len(results)} search result row(s) from {len(query_rows)} query item(s).",
        )
    )
    return state


def run_vector_retrieval(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    claim_rows = [claim.model_dump() if hasattr(claim, "model_dump") else dict(claim) for claim in state.claims]
    page_rows = list(state.pages)

    if not claim_rows or not page_rows:
        state.logs.append(
            RunLogEntry(
                node_name="vector_retrieval",
                status="skipped",
                message="Claims or pages were unavailable for vector retrieval.",
            )
        )
        return state

    retrieved_rows = retrieve_chunks_for_claims(claim_rows, page_rows, artifact_root / "agent_5b" / "vector_index")
    state.vector_chunks = retrieved_rows
    _save_csv(retrieved_rows, artifact_root / "agent_5b" / "vector_retrieval.csv")
    state.logs.append(
        RunLogEntry(
            node_name="vector_retrieval",
            status="completed",
            message=f"Retrieved {len(retrieved_rows)} vector chunk row(s) from {len(page_rows)} page row(s).",
        )
    )
    return state


def run_evidence_fetcher(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    result_rows = [result.model_dump() if hasattr(result, "model_dump") else dict(result) for result in state.search_results]

    if not result_rows:
        state.logs.append(
            RunLogEntry(
                node_name="evidence_fetcher",
                status="skipped",
                message="No search results were available for evidence extraction.",
            )
        )
        return state

    filtered = filter_low_quality_sources(result_rows)
    selected = select_best_results(filtered)
    evidence_rows = extract_all_evidence(selected)

    state.evidence_documents = []
    state.evidence_snippets = []
    state.ranked_evidence = evidence_rows
    _save_csv(evidence_rows, artifact_root / "agent_6" / "evidence_candidates.csv")
    state.logs.append(
        RunLogEntry(
            node_name="evidence_fetcher",
            status="completed",
            message=f"Extracted evidence for {len(evidence_rows)} selected search result(s).",
        )
    )
    return state


def run_reranker(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    claim_source = state.claims or state.normalized_claims or state.claims_candidates
    claim_rows = [claim.model_dump() if hasattr(claim, "model_dump") else dict(claim) for claim in claim_source]
    evidence_rows = [evidence.model_dump() if hasattr(evidence, "model_dump") else dict(evidence) for evidence in state.ranked_evidence]

    if not claim_rows or not evidence_rows:
        state.logs.append(
            RunLogEntry(
                node_name="reranker",
                status="skipped",
                message="Claims or evidence were unavailable for reranking.",
            )
        )
        return state

    claim_lookup = {claim["normalized_claim_id"]: claim for claim in claim_rows}
    usable_evidence = filter_usable_evidence(claim_lookup, evidence_rows)
    ranked_rows = rerank_evidence(claim_lookup, usable_evidence)
    state.ranked_evidence = ranked_rows
    _save_csv(ranked_rows, artifact_root / "agent_7" / "ranked_evidence.csv")
    state.logs.append(
        RunLogEntry(
            node_name="reranker",
            status="completed",
            message=f"Ranked {len(ranked_rows)} evidence row(s) from {len(usable_evidence)} usable evidence item(s).",
        )
    )
    return state


def run_evidence_analyzer(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    claim_source = state.claims or state.normalized_claims or state.claims_candidates
    claim_rows = [claim.model_dump() if hasattr(claim, "model_dump") else dict(claim) for claim in claim_source]
    evidence_rows = [row.model_dump() if hasattr(row, "model_dump") else dict(row) for row in state.ranked_evidence]

    if not claim_rows or not evidence_rows:
        state.logs.append(
            RunLogEntry(
                node_name="evidence_analyzer",
                status="skipped",
                message="Claims or evidence were unavailable for analysis.",
            )
        )
        return state

    claim_lookup = build_claim_lookup(claim_rows)
    grouped_evidence = group_top_evidence(evidence_rows, 3)
    disable_cache = str(__import__("os").getenv("PIPELINE_DISABLE_CACHE", "0")).strip() == "1"
    cache_path = artifact_root / "agent_8" / "assessment_cache.json"
    assessment_cache = {} if disable_cache else load_assessment_cache(cache_path)
    assessments = analyze_all_claims(claim_lookup, grouped_evidence, assessment_cache)
    state.claim_assessments = assessments
    _save_csv(assessments, artifact_root / "agent_8" / "claim_assessments.csv")
    if not disable_cache:
        save_assessment_cache(assessment_cache, cache_path)
    state.logs.append(
        RunLogEntry(
            node_name="evidence_analyzer",
            status="completed",
            message=f"Created {len(assessments)} claim assessment row(s).",
        )
    )
    return state


def run_judge(state: PipelineState) -> PipelineState:
    artifact_root = artifact_root_for_company(state.company_name)
    if not state.claim_assessments:
        state.logs.append(
            RunLogEntry(
                node_name="judge",
                status="skipped",
                message="No claim assessments were available for final aggregation.",
            )
        )
        return state

    final_report = build_final_report(artifact_root, state.claim_assessments)
    state.final_report = final_report
    save_final_report_artifacts(artifact_root, final_report)
    state.logs.append(
        RunLogEntry(
            node_name="judge",
            status="completed",
            message=f"Built final report for {final_report['total_claims_analyzed']} claim(s).",
        )
    )
    return state


__all__ = [
    "run_claim_extractor",
    "run_claim_normalizer",
    "run_document_loader",
    "run_evidence_analyzer",
    "run_evidence_fetcher",
    "run_judge",
    "run_query_generator",
    "run_reranker",
    "run_web_search",
]
