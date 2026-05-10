from __future__ import annotations

import json
import os
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
    summary_text = load_text(summary_path)
    report = load_json(report_path)

    st.subheader("Latest Report")
    if summary_text:
        st.markdown(summary_text)
    else:
        st.warning("No report found yet for this company.")

    if report:
        cols = st.columns(5)
        cols[0].metric("Claims", report.get("total_claims_analyzed", 0))
        cols[1].metric("Supported", report.get("label_counts", {}).get("SUPPORTED", 0))
        cols[2].metric("Unverified", report.get("label_counts", {}).get("UNVERIFIED", 0))
        cols[3].metric("Direct", report.get("evidence_relevance_counts", {}).get("DIRECT", 0))
        cols[4].metric("Indirect", report.get("evidence_relevance_counts", {}).get("INDIRECT", 0))

        with st.expander("Raw JSON"):
            st.json(report)


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
