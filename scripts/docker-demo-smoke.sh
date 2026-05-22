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

echo "==> CivicCode rejects forged staff headers on the published demo port"
staff_status="$(
  curl -sS -o /dev/null -w "%{http_code}" \
    -H "X-CivicCode-Role: staff" \
    -H "X-CivicCode-Actor: clerk@portland.example.gov" \
    "${BASE_URL}/api/v1/civiccode/staff/audit-events"
)"
if [[ "$staff_status" != "403" ]]; then
  echo "Expected forged staff headers on ${BASE_URL} to fail with HTTP 403; got HTTP ${staff_status}." >&2
  exit 1
fi

if [[ "${CIVICCODE_DOCKER_STAFF_SMOKE:-0}" == "1" ]]; then
  echo "==> CivicCode seeded staff workspace inside the API container"
  project_args=()
  if [[ -n "${COMPOSE_PROJECT_NAME:-}" ]]; then
    project_args=(-p "${COMPOSE_PROJECT_NAME}")
  fi
  docker compose "${project_args[@]}" exec -T api curl -fsS \
    -H "X-CivicCode-Role: staff" \
    -H "X-CivicCode-Actor: clerk@portland.example.gov" \
    "http://127.0.0.1:8000/staff/code" | grep -q "Code lifecycle command center"
fi

echo "DOCKER-DEMO-SMOKE: PASSED"
