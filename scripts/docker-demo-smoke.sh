#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${TOWNLIGHT_CODE_SMOKE_BASE_URL:-http://127.0.0.1:8000}"

echo "==> TownlightCode Docker demo health"
for _ in $(seq 1 60); do
  if curl -fsS "${BASE_URL}/health" | grep -q '"service":"townlight_code"'; then
    break
  fi
  sleep 2
done
curl -fsS "${BASE_URL}/health" | grep -q '"service":"townlight_code"'

echo "==> TownlightCode seeded public lookup"
curl -fsS "${BASE_URL}/townlight_code/search?q=13.40.020" | grep -q "Backyard Livestock"
curl -fsS "${BASE_URL}/townlight_code/sections/13.40.020" | grep -q "Plain-language summary"

echo "==> TownlightCode rejects forged staff headers on the published demo port"
staff_status="$(
  curl -sS -o /dev/null -w "%{http_code}" \
    -H "X-Townlight-Code-Role: staff" \
    -H "X-Townlight-Code-Actor: clerk@portland.example.gov" \
    "${BASE_URL}/api/v1/townlight_code/staff/audit-events"
)"
if [[ "$staff_status" != "403" ]]; then
  echo "Expected forged staff headers on ${BASE_URL} to fail with HTTP 403; got HTTP ${staff_status}." >&2
  exit 1
fi

if [[ "${TOWNLIGHT_CODE_DOCKER_STAFF_SMOKE:-0}" == "1" ]]; then
  echo "==> TownlightCode seeded staff workspace inside the API container"
  project_args=()
  if [[ -n "${COMPOSE_PROJECT_NAME:-}" ]]; then
    project_args=(-p "${COMPOSE_PROJECT_NAME}")
  fi
  docker compose "${project_args[@]}" exec -T api curl -fsS \
    -H "X-Townlight-Code-Role: staff" \
    -H "X-Townlight-Code-Actor: clerk@portland.example.gov" \
    "http://127.0.0.1:8000/staff/code" | grep -q "Code lifecycle command center"
fi

echo "DOCKER-DEMO-SMOKE: PASSED"
