"""Rehearse Docker/PostgreSQL backup and restore without touching source data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REHEARSAL_ROOT = ROOT / ".docker-backup-restore-rehearsal"


@dataclass(frozen=True)
class RehearsalConfig:
    rehearsal_root: Path
    run_id: str
    compose_file: Path
    project_directory: Path
    compose_project_name: str | None
    postgres_service: str
    postgres_user: str
    postgres_db: str
    keep_restore_database: bool

    @property
    def run_root(self) -> Path:
        return self.rehearsal_root / self.run_id

    @property
    def backup_root(self) -> Path:
        return self.run_root / "backup"

    @property
    def dump_path(self) -> Path:
        return self.backup_root / "civiccode-postgres.dump"

    @property
    def manifest_path(self) -> Path:
        return self.backup_root / "civiccode-docker-backup-manifest.json"

    @property
    def verification_path(self) -> Path:
        return self.run_root / "restore-verification.json"

    @property
    def restore_db(self) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", self.run_id).strip("_").lower() or "run"
        return f"civiccode_restore_{safe}"[:60]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rehearse Docker Compose PostgreSQL backup and restore for Townlight Code."
    )
    parser.add_argument("--rehearsal-root", default=str(DEFAULT_REHEARSAL_ROOT))
    parser.add_argument("--run-id", default=f"run-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}")
    parser.add_argument("--compose-file", default="docker-compose.yml")
    parser.add_argument("--project-directory", default=".")
    parser.add_argument("--compose-project-name", default=None)
    parser.add_argument("--postgres-service", default="postgres")
    parser.add_argument("--postgres-user", default=None)
    parser.add_argument("--postgres-db", default=None)
    parser.add_argument("--keep-restore-database", action="store_true")
    parser.add_argument("--print-only", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    env_values = _read_env_file(ROOT / "docker.env.example") | _read_env_file(ROOT / ".env")
    config = RehearsalConfig(
        rehearsal_root=Path(args.rehearsal_root),
        run_id=args.run_id,
        compose_file=Path(args.compose_file),
        project_directory=Path(args.project_directory),
        compose_project_name=args.compose_project_name or os.environ.get("COMPOSE_PROJECT_NAME"),
        postgres_service=args.postgres_service,
        postgres_user=args.postgres_user
        or os.environ.get("POSTGRES_USER")
        or env_values.get("POSTGRES_USER")
        or "civiccode",
        postgres_db=args.postgres_db
        or os.environ.get("POSTGRES_DB")
        or env_values.get("POSTGRES_DB")
        or "civiccode",
        keep_restore_database=args.keep_restore_database,
    )

    print_plan(config)
    if args.print_only:
        print("DOCKER-BACKUP-RESTORE-REHEARSAL: PRINT-ONLY")
        return 0

    try:
        run_rehearsal(config)
    except RehearsalError as exc:
        print(f"DOCKER-BACKUP-RESTORE-REHEARSAL: FAILED - {exc}")
        return 1 if args.strict else 0
    print("DOCKER-BACKUP-RESTORE-REHEARSAL: PASSED")
    return 0


def print_plan(config: RehearsalConfig) -> None:
    compose = _compose_base(config)
    print("Townlight Code Docker/PostgreSQL backup/restore rehearsal")
    print(f"Run id: {config.run_id}")
    print(f"Rehearsal root: {_display_path(config.run_root)}")
    print(f"PostgreSQL service: {config.postgres_service}")
    if config.compose_project_name:
        print(f"Compose project: {config.compose_project_name}")
    print(f"Source database: {config.postgres_db}")
    print(f"Restore database: {config.restore_db}")
    print(f"Backup dump: {_display_path(config.dump_path)}")
    print(f"Backup manifest: {_display_path(config.manifest_path)}")
    print("Plan:")
    print("  1. Confirm Docker Compose can see the postgres service.")
    print(
        "  2. Run pg_dump from the postgres container into "
        f"{_display_path(config.dump_path)}."
    )
    print(
        "  3. Create a temporary restore database, run pg_restore into it, "
        "and verify restored application tables."
    )
    print("  4. Drop the temporary restore database unless --keep-restore-database is set.")
    print("Representative commands:")
    print(f"  {' '.join(compose)} ps {config.postgres_service}")
    print(
        f"  {' '.join(compose)} exec -T {config.postgres_service} "
        f"pg_dump -U {config.postgres_user} -d {config.postgres_db} -Fc > "
        f"{_display_path(config.dump_path)}"
    )
    print(
        f"  {' '.join(compose)} exec -T {config.postgres_service} "
        f"createdb -U {config.postgres_user} {config.restore_db}"
    )
    print(
        f"  {' '.join(compose)} exec -T {config.postgres_service} "
        f"pg_restore -U {config.postgres_user} -d {config.restore_db} < "
        f"{_display_path(config.dump_path)}"
    )
    print(
        "Fix path: if a step fails, keep the run directory, confirm Docker Desktop "
        "is running, start the stack with 'docker compose up -d', inspect "
        "'docker compose logs postgres api', then rerun with a new run id."
    )


def run_rehearsal(config: RehearsalConfig) -> None:
    config.backup_root.mkdir(parents=True, exist_ok=True)
    if config.dump_path.exists():
        raise RehearsalError(
            f"Refusing to overwrite existing dump: {_display_path(config.dump_path)}. "
            "Choose a new --run-id or remove the old rehearsal directory yourself."
        )

    _run(_compose_base(config) + ["ps", config.postgres_service], cwd=config.project_directory)
    _dump_database(config)
    _run_sql(config, f"DROP DATABASE IF EXISTS {_quote_identifier(config.restore_db)};")
    try:
        _run(
            _compose_base(config)
            + [
                "exec",
                "-T",
                config.postgres_service,
                "createdb",
                "-U",
                config.postgres_user,
                config.restore_db,
            ],
            cwd=config.project_directory,
        )
        _restore_database(config)
        restored_tables = _list_restored_application_tables(config)
        if not restored_tables:
            raise RehearsalError(
                "The restore database has no application tables after pg_restore. "
                "Confirm the source Compose stack has run migrations and seeded or created data."
            )
        _write_manifest(config=config, restored_tables=restored_tables)
    finally:
        if not config.keep_restore_database:
            _run_sql(config, f"DROP DATABASE IF EXISTS {_quote_identifier(config.restore_db)};")


def _dump_database(config: RehearsalConfig) -> None:
    command = _compose_base(config) + [
        "exec",
        "-T",
        config.postgres_service,
        "pg_dump",
        "-U",
        config.postgres_user,
        "-d",
        config.postgres_db,
        "-Fc",
    ]
    with config.dump_path.open("wb") as handle:
        result = subprocess.run(
            command,
            cwd=config.project_directory,
            check=False,
            stdout=handle,
            stderr=subprocess.PIPE,
        )
    if result.returncode != 0:
        raise RehearsalError(_format_failure(command, result.stderr.decode(errors="replace")))
    if config.dump_path.stat().st_size == 0:
        raise RehearsalError("pg_dump created an empty dump file; refusing to continue.")


def _restore_database(config: RehearsalConfig) -> None:
    command = _compose_base(config) + [
        "exec",
        "-T",
        config.postgres_service,
        "pg_restore",
        "-U",
        config.postgres_user,
        "-d",
        config.restore_db,
    ]
    with config.dump_path.open("rb") as handle:
        result = subprocess.run(
            command,
            cwd=config.project_directory,
            check=False,
            stdin=handle,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    if result.returncode != 0:
        raise RehearsalError(_format_failure(command, result.stderr.decode(errors="replace")))


def _run_sql(config: RehearsalConfig, sql: str) -> None:
    _run(
        _compose_base(config)
        + [
            "exec",
            "-T",
            config.postgres_service,
            "psql",
            "-U",
            config.postgres_user,
            "-d",
            "postgres",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        cwd=config.project_directory,
    )


def _list_restored_application_tables(config: RehearsalConfig) -> list[str]:
    command = _compose_base(config) + [
        "exec",
        "-T",
        config.postgres_service,
        "psql",
        "-U",
        config.postgres_user,
        "-d",
        config.restore_db,
        "-v",
        "ON_ERROR_STOP=1",
        "-At",
        "-c",
        (
            "SELECT table_schema || '.' || table_name "
            "FROM information_schema.tables "
            "WHERE table_type='BASE TABLE' "
            "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
            "ORDER BY table_schema, table_name;"
        ),
    ]
    result = _run(command, cwd=config.project_directory)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _write_manifest(*, config: RehearsalConfig, restored_tables: list[str]) -> None:
    verification = {
        "service": "civiccode",
        "checked_at": datetime.now(UTC).isoformat(),
        "restore_database": config.restore_db,
        "restored_application_tables": restored_tables,
        "restore_database_dropped": not config.keep_restore_database,
    }
    config.verification_path.write_text(
        json.dumps(verification, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest = {
        "service": "civiccode",
        "created_at": datetime.now(UTC).isoformat(),
        "source": "docker-compose-postgres",
        "postgres_service": config.postgres_service,
        "source_database": config.postgres_db,
        "restore_database": config.restore_db,
        "dump": {
            "path": config.dump_path.relative_to(config.run_root).as_posix(),
            "size": config.dump_path.stat().st_size,
            "sha256": _sha256(config.dump_path),
        },
        "verification": config.verification_path.relative_to(config.run_root).as_posix(),
        "restored_application_tables": restored_tables,
    }
    config.manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _compose_base(config: RehearsalConfig) -> list[str]:
    command = [
        "docker",
        "compose",
        "-f",
        str(config.compose_file),
        "--project-directory",
        str(config.project_directory),
    ]
    if config.compose_project_name:
        command.extend(["-p", config.compose_project_name])
    return command


def _run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RehearsalError(_format_failure(command, result.stderr or result.stdout))
    return result


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _format_failure(command: list[str], detail: str) -> str:
    cleaned = detail.strip() or "command failed without output"
    return f"Command failed: {' '.join(command)}\n{cleaned}"


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


class RehearsalError(RuntimeError):
    """Raised when an operator-facing rehearsal step fails."""


if __name__ == "__main__":
    raise SystemExit(main())
