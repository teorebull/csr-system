from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Queue

import streamlit as st

from src.utils.company import artifact_root_for_company


PROJECT_ROOT = Path(__file__).resolve().parent
RUN_GRAPH = PROJECT_ROOT / "run_graph.py"
NODE_LABELS = {
    "load_documents": "Agent 1: Document Loader",
    "extract_claims": "Agent 2: Claim Extractor",
    "normalize_claims": "Agent 3: Claim Normalizer",
    "generate_queries": "Agent 4: Query Generator",
    "search_evidence": "Agent 5: Web Search",
    "fetch_evidence": "Agent 6: Evidence Fetcher",
    "rerank_evidence": "Agent 7: Reranker",
    "analyze_claims": "Agent 8: Evidence Analyzer",
    "aggregate_report": "Agent 9: Judge / Final Report",
}
NODE_ORDER = list(NODE_LABELS.keys())
COMPANIES = ["Microsoft", "Tesla", "Meta", "Amazon"]
AGENT_9_MODELS = ["qwen2.5:14b", "gemini-2.0-flash", "gemini-2.0-pro"]


@dataclass
class RunResult:
    returncode: int
    output: str


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def claim_preview(text: str, max_length: int = 100) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= max_length:
        return value
    return f"{value[:max_length]}..."


def evidence_link(title: str, url: str) -> str:
    clean_title = re.sub(r"\s+", " ", str(title or "")).strip() or "External evidence"
    clean_url = str(url or "").strip()
    if not clean_url:
        return "No selected source"
    return f"[{clean_title}]({clean_url})"


def set_query_param(name: str, value: str) -> None:
    if value:
        st.query_params[name] = value
    elif name in st.query_params:
        del st.query_params[name]


def get_query_param(name: str) -> str:
    value = st.query_params.get(name, "")
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def available_companies() -> list[str]:
    companies = []
    for company in COMPANIES:
        if (PROJECT_ROOT / "data" / "raw" / company.lower()).exists() or (artifact_root_for_company(company)).exists():
            companies.append(company)
    return companies or COMPANIES


def normalize_agent_name(agent_name: str) -> str:
    if agent_name in NODE_ORDER:
        return agent_name
    return NODE_ORDER[0]


def run_pipeline_command(
    company: str,
    start_at: str,
    stop_at: str,
    no_cache: bool,
    max_documents: int,
    max_pages_per_document: int,
    max_page_chars: int,
    agent_9_provider: str,
    agent_9_model: str,
) -> RunResult:
    args = [
        sys.executable,
        str(RUN_GRAPH),
        "--company",
        company,
        "--mode",
        "normal",
        "--start-at",
        start_at,
        "--stop-at",
        stop_at,
        "--max-documents",
        str(max_documents),
        "--max-pages-per-document",
        str(max_pages_per_document),
        "--max-page-chars",
        str(max_page_chars),
    ]
    if no_cache:
        args.append("--no-cache")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["AGENT_9_PROVIDER"] = agent_9_provider
    env["AGENT_9_MODEL"] = agent_9_model
    if agent_9_provider == "gemini":
        env["AGENT_9_GEMINI_MODEL"] = agent_9_model

    process = subprocess.Popen(
        args,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )

    output_lines: list[str] = []
    if process.stdout is not None:
        for line in process.stdout:
            output_lines.append(line)
            queue: Queue[str] | None = st.session_state.get("progress_queue")
            if queue is not None:
                queue.put(line)

    returncode = process.wait()
    return RunResult(returncode=returncode, output="".join(output_lines))


def init_state() -> None:
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("progress_lines", [])
    st.session_state.setdefault("progress_queue", Queue())
    st.session_state.setdefault("last_returncode", None)
    st.session_state.setdefault("last_company", "Microsoft")


def update_progress_from_queue() -> None:
    queue: Queue[str] = st.session_state.get("progress_queue")
    if queue is None:
        return
    while True:
        try:
            line = queue.get_nowait()
        except Empty:
            break
        st.session_state.progress_lines.append(line.rstrip())


def show_progress_panel() -> None:
    st.subheader("Live Progress")
    if not st.session_state.progress_lines:
        st.info("No workflow run started yet.")
        return

    current_agent = ""
    for line in reversed(st.session_state.progress_lines):
        if line.startswith("[") and "]" in line:
            tag = line.split("]", 1)[0].strip("[")
            if tag in NODE_LABELS:
                current_agent = NODE_LABELS[tag]
                break

    if current_agent:
        st.success(f"Current stage: {current_agent}")
    else:
        st.info("Workflow running or completed.")

    st.text_area(
        "Run log",
        value="\n".join(st.session_state.progress_lines[-200:]),
        height=320,
    )


def render_progress_snapshot(progress_placeholder, log_placeholder) -> None:
    current_agent = ""
    for line in reversed(st.session_state.progress_lines):
        if line.startswith("[") and "]" in line:
            tag = line.split("]", 1)[0].strip("[")
            if tag in NODE_LABELS:
                current_agent = NODE_LABELS[tag]
                break

    with progress_placeholder.container():
        if current_agent:
            st.success(f"Current stage: {current_agent}")
        else:
            st.info("Workflow running or completed.")

    with log_placeholder.container():
        st.text_area(
            "Run log",
            value="\n".join(st.session_state.progress_lines[-200:]),
            height=320,
        )


def show_report(company: str) -> None:
    artifact_root = artifact_root_for_company(company)
    summary_path = artifact_root / "agent_9" / "final_summary.md"
    report_path = artifact_root / "agent_9" / "final_report.json"
    csr_path = artifact_root / "agent_9" / "final_csr_assessment.csv"
    environmental_path = artifact_root / "agent_9" / "final_environmental_subassessment.csv"
    summary_text = load_text(summary_path)
    report = load_json(report_path)
    csr_rows = load_csv_rows(csr_path)
    environmental_rows = load_csv_rows(environmental_path)

    st.subheader("Latest Report")
    if report:
        cols = st.columns(5)
        cols[0].metric("Claims", report.get("total_claims_analyzed", 0))
        cols[1].metric("Supported", report.get("label_counts", {}).get("SUPPORTED", 0))
        cols[2].metric("Unverified", report.get("label_counts", {}).get("UNVERIFIED", 0))
        cols[3].metric("Direct", report.get("evidence_relevance_counts", {}).get("DIRECT", 0))
        cols[4].metric("Indirect", report.get("evidence_relevance_counts", {}).get("INDIRECT", 0))

    summary_tab, claims_tab, environmental_tab, raw_tab = st.tabs([
        "Final Summary",
        "Claim Explorer",
        "Environmental Claim Explorer",
        "Raw JSON",
    ])

    with summary_tab:
        if summary_text:
            st.markdown(summary_text)
            st.caption("To inspect any claim in detail, open the Claim Explorer and select the Claim ID.")
        else:
            st.warning("No report found yet for this company.")

    with claims_tab:
        render_claim_explorer(
            title="Claims Reference",
            description="Click or select a Claim ID to inspect the full claim metadata, source passage, external evidence, and assessment rationale.",
            rows=csr_rows,
            query_param_name="claim_id",
            show_environmental_context=False,
        )

    with environmental_tab:
        st.caption("Environmental greenwashing-risk sub-assessment only. Non-environmental claims are excluded from this view.")
        render_claim_explorer(
            title="Environmental Claims Reference",
            description="Click or select a Claim ID to inspect the full claim metadata, source passage, external evidence, and assessment rationale.",
            rows=environmental_rows,
            query_param_name="env_claim_id",
            show_environmental_context=True,
        )

    with raw_tab:
        if report:
            st.json(report)
        else:
            st.info("No raw report JSON found yet.")


def render_claim_explorer(
    title: str,
    description: str,
    rows: list[dict[str, str]],
    query_param_name: str,
    show_environmental_context: bool,
) -> None:
    st.markdown(f"### {title}")
    st.write(description)

    if not rows:
        st.warning("No claim assessment rows found for this view.")
        return

    table_rows = []
    for row in rows:
        table_rows.append(
            {
                "normalized_claim_id": row.get("normalized_claim_id", ""),
                "claim_preview": claim_preview(row.get("claim_text", ""), 100),
                "claim_family": row.get("claim_family", ""),
                "final_label": row.get("final_label", ""),
                "greenwashing_risk_level": row.get("greenwashing_risk_level", ""),
                "evidence_relevance": row.get("evidence_relevance", ""),
                "document_name": row.get("document_name", ""),
                "page_numbers": row.get("page_numbers", ""),
                "top_evidence_title": row.get("top_evidence_title", ""),
            }
        )

    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    claim_ids = [row.get("normalized_claim_id", "") for row in rows if row.get("normalized_claim_id")]
    requested_claim_id = get_query_param(query_param_name)
    default_claim_id = requested_claim_id if requested_claim_id in claim_ids else claim_ids[0]
    selected_claim_id = st.selectbox(
        "Select a Claim ID",
        claim_ids,
        index=claim_ids.index(default_claim_id),
        key=f"select_{query_param_name}",
    )
    set_query_param(query_param_name, selected_claim_id)

    selected_row = next((row for row in rows if row.get("normalized_claim_id") == selected_claim_id), rows[0])
    render_claim_detail_card(selected_row, show_environmental_context=show_environmental_context)


def render_claim_detail_card(row: dict[str, str], show_environmental_context: bool) -> None:
    st.markdown(f"#### Claim Card: `{row.get('normalized_claim_id', 'N/A')}`")

    left, right = st.columns([1, 1])
    with left:
        st.markdown(f"**Claim ID:** `{row.get('normalized_claim_id', 'N/A')}`")
        st.markdown(f"**Domain:** `{row.get('claim_family', 'N/A') or 'N/A'}`")
        st.markdown(f"**Corporate source:** {row.get('document_name', 'N/A') or 'N/A'}")
        st.markdown(f"**Document ID:** `{row.get('document_id', 'N/A') or 'N/A'}`")
        st.markdown(f"**Page numbers:** `{row.get('page_numbers', 'N/A') or 'N/A'}`")
        st.markdown(f"**Source locations:** `{row.get('source_locations', 'N/A') or 'N/A'}`")
    with right:
        st.markdown(f"**Final label:** `{row.get('final_label', 'N/A') or 'N/A'}`")
        signal_label = "Greenwashing-risk level" if show_environmental_context else "CSR credibility signal"
        st.markdown(f"**{signal_label}:** `{row.get('greenwashing_risk_level', 'N/A') or 'N/A'}`")
        st.markdown(f"**Evidence relevance:** `{row.get('evidence_relevance', 'N/A') or 'N/A'}`")
        st.markdown(f"**Stance:** `{row.get('stance', 'N/A') or 'N/A'}`")
        st.markdown(f"**Materiality score:** `{row.get('materiality_score', 'N/A') or 'N/A'}`")
        st.markdown(f"**Judgment score:** `{row.get('judgment_score', 'N/A') or 'N/A'}`")

    st.markdown(f"**Full claim text:** {row.get('claim_text', 'N/A') or 'N/A'}")
    st.markdown(f"**External evidence:** {evidence_link(row.get('top_evidence_title', ''), row.get('top_evidence_url', ''))}")

    with st.expander("Source excerpt", expanded=True):
        st.write(row.get("source_excerpts", "N/A") or "N/A")

    with st.expander("Justification", expanded=True):
        st.write(row.get("justification", "N/A") or "N/A")

    risk_reasoning = str(row.get("risk_reasoning", "")).strip()
    if risk_reasoning:
        with st.expander("Risk reasoning", expanded=False):
            st.write(risk_reasoning)


def main() -> None:
    st.set_page_config(page_title="CSR System", layout="wide")
    init_state()

    st.title("CSR System Workflow")
    st.caption("Run the pipeline, watch the agent progress, and inspect the latest report.")

    companies = available_companies()
    default_company_index = companies.index(st.session_state.get("last_company", companies[0])) if st.session_state.get("last_company", companies[0]) in companies else 0

    with st.sidebar:
        st.header("Run Settings")
        company = st.selectbox("Company", companies, index=default_company_index)
        start_at = st.selectbox("Start at", NODE_ORDER, index=0)
        stop_at = st.selectbox("Stop at", NODE_ORDER, index=len(NODE_ORDER) - 1)
        agent_9_provider = st.selectbox("Final report provider", ["ollama", "gemini"], index=0)
        default_model_index = 1 if agent_9_provider == "gemini" else 0
        agent_9_model = st.selectbox("Final report model", AGENT_9_MODELS, index=default_model_index)
        no_cache = st.checkbox("Disable cache", value=False)
        max_documents = st.number_input("Max documents", min_value=0, value=0, step=1)
        max_pages_per_document = st.number_input("Max pages per document", min_value=0, value=0, step=1)
        max_page_chars = st.number_input("Max page chars", min_value=0, value=0, step=100)
        run_button = st.button("Run workflow", type="primary", use_container_width=True)

        st.markdown("### Defaults")
        st.write("Start at Agent 1")
        st.write("No limits on docs/pages/chars")
        st.write(f"Provider: {agent_9_provider}")
        st.write(f"Model: {agent_9_model}")

    if run_button:
        if st.session_state.running:
            st.warning("A run is already in progress.")
        else:
            st.session_state.running = True
            st.session_state.last_company = company
            st.session_state.progress_lines = []
            st.session_state.progress_queue = Queue()
            progress_placeholder = st.empty()
            log_placeholder = st.empty()
            result_box = st.empty()
            queue: Queue[str] = st.session_state.progress_queue
            with st.spinner("Running workflow..."):
                args = [
                    sys.executable,
                    str(RUN_GRAPH),
                    "--company",
                    company,
                    "--mode",
                    "normal",
                    "--start-at",
                    normalize_agent_name(start_at),
                    "--stop-at",
                    normalize_agent_name(stop_at),
                    "--max-documents",
                    str(int(max_documents)),
                    "--max-pages-per-document",
                    str(int(max_pages_per_document)),
                    "--max-page-chars",
                    str(int(max_page_chars)),
                ]
                if no_cache:
                    args.append("--no-cache")

                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"
                env["COMPANY_NAME"] = company
                env["AGENT_9_PROVIDER"] = agent_9_provider
                env["AGENT_9_MODEL"] = agent_9_model
                if agent_9_provider == "gemini":
                    env["AGENT_9_GEMINI_MODEL"] = agent_9_model
                process = subprocess.Popen(
                    args,
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    env=env,
                )

                output_lines: list[str] = []
                if process.stdout is not None:
                    for line in process.stdout:
                        output_lines.append(line)
                        queue.put(line)
                        try:
                            st.session_state.progress_lines.append(line.rstrip())
                        except Exception:
                            pass
                        render_progress_snapshot(progress_placeholder, log_placeholder)

                returncode = process.wait()
                result = RunResult(returncode=returncode, output="".join(output_lines))
            st.session_state.last_returncode = result.returncode
            st.session_state.progress_lines.extend(result.output.splitlines())
            st.session_state.running = False
            if result.returncode == 0:
                st.success("Workflow completed successfully.")
            else:
                st.error(f"Workflow exited with code {result.returncode}.")

    update_progress_from_queue()

    left, right = st.columns([1, 2])
    with left:
        show_progress_panel()
    with right:
        show_report(st.session_state.last_company)


if __name__ == "__main__":
    main()
