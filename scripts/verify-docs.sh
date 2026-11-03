#!/usr/bin/env bash
set -euo pipefail

required=(
  "README.md"
  "README.txt"
  "CHANGELOG.md"
  "CONTRIBUTING.md"
  "LICENSE"
  "LICENSE-CODE"
  "LICENSE-DOCS"
  ".gitignore"
  ".dockerignore"
  "AGENTS.md"
  "USER-MANUAL.md"
  "SECURITY.md"
  "SUPPORT.md"
  "CODE_OF_CONDUCT.md"
  "docs/RECONCILIATION.md"
  "docs/MILESTONES.md"
  "docs/IMPLEMENTATION_PLAN.md"
  "docs/github-discussions-seed.md"
  "scripts/verify-release.sh"
  "Dockerfile"
  "docker-compose.yml"
  "docker.env.example"
  "scripts/docker-demo-smoke.sh"
  "scripts/check_docker_backup_restore_rehearsal.py"
  "scripts/start_docker_backup_restore_rehearsal.ps1"
  "scripts/start_docker_backup_restore_rehearsal.sh"
  "docs/index.html"
  "MILESTONE_1_DONE.md"
  "MILESTONE_3_DONE.md"
  "MILESTONE_4_DONE.md"
  "MILESTONE_5_DONE.md"
  "MILESTONE_6_DONE.md"
  "MILESTONE_7_DONE.md"
  "MILESTONE_8_DONE.md"
  "MILESTONE_9_DONE.md"
  "MILESTONE_10_DONE.md"
  "MILESTONE_11_DONE.md"
  "MILESTONE_12_DONE.md"
  "MILESTONE_13_DONE.md"
  "MILESTONE_14_DONE.md"
  "pyproject.toml"
  "townlight_code/__init__.py"
  "townlight_code/main.py"
  "townlight_code/citation_contract.py"
  "townlight_code/qa_harness.py"
  "townlight_code/plain_language.py"
  "townlight_code/ordinance_handoff.py"
  "townlight_code/import_connectors.py"
  "townlight_code/public_exports.py"
  "townlight_code/public_discovery.py"
  "townlight_code/public_lookup.py"
  "townlight_code/staff_workbench.py"
  "townlight_code/source_registry.py"
  "townlight_code/section_lifecycle.py"
  "townlight_code/models.py"
  "townlight_code/migrations/alembic.ini"
  "townlight_code/migrations/env.py"
  "townlight_code/migrations/guards.py"
  "townlight_code/migrations/versions/townlight_code_0001_schema.py"
  "townlight_code/migrations/versions/townlight_code_0002_source_registry_records.py"
  "townlight_code/migrations/versions/townlight_code_0003_popular_question_records.py"
  "townlight_code/migrations/versions/townlight_code_0004_section_lifecycle_records.py"
  "tests/fixtures/milestone_12/csv_bundle.json"
  "tests/fixtures/milestone_12/official_html_extract.json"
  "tests/fixtures/milestone_12/broken_missing_section.json"
  "tests/test_popular_questions_related_discovery.py"
)

echo "==> Required-artifact check"
for file in "${required[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "FAIL: missing required artifact: $file" >&2
    exit 1
  fi
done

echo "==> Current-facing shipped/planned truth check"
current_files=("README.md" "README.txt" "USER-MANUAL.md" "docs/index.html")
bad_markers=(
  "TownlightCode is shipping"
  "Shipping v0.1.0"
  "scaffold only"
  "not installable yet"
  "code answers are available"
  "municipal code answers are available"
  "uncited answers are available"
  "legal advice is available"
  "live LLM calls are enabled"
  "public lookup UI is available"
  "staff notes are public"
  "public staff-note visibility"
  "plain-language summaries are law"
  "summaries provide legal advice"
  "pending ordinance language is adopted law"
  "automatic ordinance codification is available"
  "current product line"
  "current durable operational-state product release"
  "current durable operational-state product line"
)

for file in "${current_files[@]}"; do
  for marker in "${bad_markers[@]}"; do
    if grep -Fqi "$marker" "$file"; then
      echo "FAIL: stale/planned-as-shipped marker '$marker' found in $file" >&2
      exit 1
    fi
  done
done

echo "PASS"
