#!/usr/bin/env bash
set -euo pipefail

rehearsal_root=".docker-backup-restore-rehearsal"
run_id="run-$(date -u +%Y%m%d-%H%M%S)"
compose_project_name=""
strict=1
print_only=0
keep_restore_database=0

usage() {
  cat <<'EOF'
Usage: bash scripts/start_docker_backup_restore_rehearsal.sh [--rehearsal-root PATH] [--run-id ID] [--compose-project-name NAME] [--print-only] [--keep-restore-database]

Creates a Docker Compose PostgreSQL backup/restore rehearsal using pg_dump,
restores into a temporary database, verifies restored tables, and drops the
temporary restore database unless explicitly told to keep it.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rehearsal-root)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --rehearsal-root." >&2
        exit 2
      fi
      rehearsal_root="$2"
      shift 2
      ;;
    --run-id)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --run-id." >&2
        exit 2
      fi
      run_id="$2"
      shift 2
      ;;
    --compose-project-name)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --compose-project-name." >&2
        exit 2
      fi
      compose_project_name="$2"
      shift 2
      ;;
    --print-only)
      print_only=1
      shift
      ;;
    --keep-restore-database)
      keep_restore_database=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"
restore_suffix="$(printf '%s' "$run_id" | sed -E 's/[^a-zA-Z0-9_]+/_/g')"

echo "CivicCode Docker/PostgreSQL backup/restore rehearsal profile"
echo "Rehearsal root: $rehearsal_root"
echo "Run id: $run_id"
if [[ -n "$compose_project_name" ]]; then
  echo "Compose project: $compose_project_name"
fi
echo "Python verifier: python scripts/check_docker_backup_restore_rehearsal.py"
echo "Backup dump: backup/civiccode-postgres.dump"
echo "Backup manifest: backup/civiccode-docker-backup-manifest.json"
echo "Restore target: temporary PostgreSQL database civiccode_restore_${restore_suffix}"
echo "Verification: pg_dump, pg_restore, restored application table list, manifest checksum"
echo "Safety: the source civiccode database is not dropped or overwritten."
echo "Fix path: if the run fails, confirm Docker Desktop is running, start the stack with docker compose up -d, inspect docker compose logs postgres api, then rerun with a new --run-id."

args=(
  "scripts/check_docker_backup_restore_rehearsal.py"
  "--rehearsal-root" "$rehearsal_root"
  "--run-id" "$run_id"
)
if [[ -n "$compose_project_name" ]]; then
  args+=("--compose-project-name" "$compose_project_name")
fi
if [[ "$strict" -eq 1 ]]; then
  args+=("--strict")
fi
if [[ "$print_only" -eq 1 ]]; then
  args+=("--print-only")
fi
if [[ "$keep_restore_database" -eq 1 ]]; then
  args+=("--keep-restore-database")
fi

cd "$repo_root"

if [[ -n "${CIVICCODE_REHEARSAL_PYTHON:-}" ]]; then
  python_cmd=("${CIVICCODE_REHEARSAL_PYTHON}")
elif [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]] && command -v py >/dev/null 2>&1; then
  python_cmd=(py -3)
elif command -v python3 >/dev/null 2>&1; then
  python_cmd=(python3)
elif command -v python >/dev/null 2>&1; then
  python_cmd=(python)
elif command -v py >/dev/null 2>&1; then
  python_cmd=(py -3)
else
  echo "Python is required for the Docker backup/restore rehearsal. Install Python 3 or rerun from Windows PowerShell with scripts/start_docker_backup_restore_rehearsal.ps1." >&2
  exit 1
fi

"${python_cmd[@]}" "${args[@]}"
