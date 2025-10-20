#!/usr/bin/env bash
set -euo pipefail
API_URL="${API_URL:-}"
if [[ -n "$API_URL" ]]; then
  echo "🩺 Cloud smoke → $API_URL/run"
  curl -sS -X POST "$API_URL/run" -H "Content-Type: application/json" \
    -d '{"risk_profile":"balanced","horizon_years":5,"context":{"demo_seed":42}}' | jq .
else
  echo "🩺 Local smoke → python -c run_pipeline"
  python - <<'PY'
from src.pipeline import run_pipeline
print(run_pipeline({"risk_profile":"balanced","horizon_years":5,"context":{"demo_seed":42}}))
PY
fi
