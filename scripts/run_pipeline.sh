#!/usr/bin/env bash
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
START_AGENT="${1:-2}"
PIPELINE_MODE="${2:-normal}"

export PIPELINE_MODE

mkdir -p "$LOG_DIR"

require_ollama() {
  python - <<'PY'
from urllib import request
import sys

try:
    request.urlopen("http://localhost:11434/api/tags", timeout=5)
except Exception:
    print("Ollama is not reachable. Start it with `ollama serve` before running LLM agents.")
    sys.exit(1)
PY
}

run_step() {
  local agent_number="$1"
  local name="$2"
  local script_path="$3"

  if [ "$agent_number" -lt "$START_AGENT" ]; then
    echo "Skipping Agent $agent_number: $name"
    return
  fi

  echo "=================================================="
  echo "Running Agent $agent_number: $name"
  echo "=================================================="

  (
    cd "$PROJECT_ROOT"
    python "$script_path"
  ) 2>&1 | tee "$LOG_DIR/agent_${agent_number}_${name}.log"
}

echo "Project root: $PROJECT_ROOT"
echo "Logs: $LOG_DIR"
echo "Starting from Agent $START_AGENT"
echo "Pipeline mode: $PIPELINE_MODE"
echo ""

run_step 2 "claim_extractor" "scripts/agent_2/extract_claims_with_llm.py"
run_step 3 "claim_normalizer" "scripts/agent_3/normalize_claims.py"
run_step 4 "query_generator" "scripts/agent_4/query_generator.py"
run_step 5 "web_search" "scripts/agent_5/web_search.py"
run_step 6 "evidence_checker" "scripts/agent_6/evidence_checker.py"
run_step 7 "reranker" "scripts/agent_7/reranker.py"

if [ "$START_AGENT" -le 8 ]; then
  require_ollama
fi

run_step 8 "evidence_analyzer" "scripts/agent_8/evidence_analyzer.py"
run_step 9 "judge_aggregator" "scripts/agent_9/judge_aggregator.py"

echo "=================================================="
echo "Pipeline completed"
echo "Final summary: $PROJECT_ROOT/data/processed/agent_9/final_summary.md"
echo "=================================================="
