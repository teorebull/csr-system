#!/usr/bin/env bash
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"

MAX_DOCUMENTS="${1:-1}"
MAX_PAGES_PER_DOCUMENT="${2:-1}"
MAX_PAGE_CHARS="${3:-2000}"

cd "$PROJECT_ROOT"
PYTHONUNBUFFERED=1 python "run_graph.py" --mode fast --max-documents "$MAX_DOCUMENTS" --max-pages-per-document "$MAX_PAGES_PER_DOCUMENT" --max-page-chars "$MAX_PAGE_CHARS" --stop-at extract_claims
