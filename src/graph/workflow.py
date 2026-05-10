from __future__ import annotations

from typing import Any

from src.graph.nodes import (
    run_claim_extractor,
    run_claim_normalizer,
    run_document_loader,
    run_evidence_analyzer,
    run_evidence_fetcher,
    run_judge,
    run_query_generator,
    run_reranker,
    run_vector_retrieval,
    run_web_search,
)
from src.schemas.state import PipelineState


WORKFLOW_NODES = [
    run_document_loader,
    run_claim_extractor,
    run_claim_normalizer,
    run_query_generator,
    run_web_search,
    run_evidence_fetcher,
    run_reranker,
    run_evidence_analyzer,
    run_judge,
]


def run_pipeline(state: PipelineState) -> PipelineState:
    """Sequential fallback runner while the LangGraph integration is assembled."""
    current_state = state
    for node in WORKFLOW_NODES:
        current_state = node(current_state)
    return current_state


def run_workflow(state: PipelineState) -> PipelineState:
    """Run the graph if available, otherwise fall back to the sequential runner."""
    try:
        workflow = build_workflow()
    except RuntimeError:
        return run_pipeline(state)

    return workflow.invoke(state)


def build_workflow() -> Any:
    """Return a LangGraph workflow when the dependency is available.

    The project keeps this function isolated so the schemas and agent code remain
    usable before LangGraph is installed.
    """
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError(
            "LangGraph is not installed. Install it to build the workflow graph."
        ) from exc

    graph = StateGraph(PipelineState)
    graph.add_node("load_documents", run_document_loader)
    graph.add_node("extract_claims", run_claim_extractor)
    graph.add_node("normalize_claims", run_claim_normalizer)
    graph.add_node("generate_queries", run_query_generator)
    graph.add_node("search_evidence", run_web_search)
    graph.add_node("fetch_evidence", run_evidence_fetcher)
    graph.add_node("rerank_evidence", run_reranker)
    graph.add_node("analyze_claims", run_evidence_analyzer)
    graph.add_node("aggregate_report", run_judge)

    graph.add_edge(START, "load_documents")
    graph.add_edge("load_documents", "extract_claims")
    graph.add_edge("extract_claims", "normalize_claims")
    graph.add_edge("normalize_claims", "generate_queries")
    graph.add_edge("generate_queries", "search_evidence")
    graph.add_edge("search_evidence", "fetch_evidence")
    graph.add_edge("fetch_evidence", "rerank_evidence")
    graph.add_edge("rerank_evidence", "analyze_claims")
    graph.add_edge("analyze_claims", "aggregate_report")
    graph.add_edge("aggregate_report", END)

    return graph.compile()
