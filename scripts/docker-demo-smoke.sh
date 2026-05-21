#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${CIVICCODE_SMOKE_BASE_URL:-http://127.0.0.1:8000}"

echo "==> CivicCode Docker demo health"
for _ in $(seq 1 60); do
  if curl -fsS "${BASE_URL}/health" | grep -q '"service":"civiccode"'; then
    break
  fi
  sleep 2
done
curl -fsS "${BASE_URL}/health" | grep -q '"service":"civiccode"'

echo "==> CivicCode seeded public lookup"
curl -fsS "${BASE_URL}/civiccode/search?q=13.40.020" | grep -q "Backyard Livestock"
curl -fsS "${BASE_URL}/civiccode/sections/13.40.020" | grep -q "Plain-language summary"

echo "==> CivicCode seeded staff workspace"
curl -fsS \
  -H "X-CivicCode-Role: staff" \
  -H "X-CivicCode-Actor: clerk@brookfield.example.gov" \
  "${BASE_URL}/staff/code" | grep -q "Code lifecycle command center"

echo "DOCKER-DEMO-SMOKE: PASSED"
