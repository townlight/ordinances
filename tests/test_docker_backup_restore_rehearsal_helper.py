"""Docker/PostgreSQL backup/restore rehearsal helper contract tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_docker_backup_restore_rehearsal_prints_non_destructive_plan(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "python",
            "scripts/check_docker_backup_restore_rehearsal.py",
            "--rehearsal-root",
            str(tmp_path),
            "--run-id",
            "print-plan",
            "--compose-project-name",
            "civiccode_print_plan",
            "--print-only",
            "--strict",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for expected in [
        "CivicCode Docker/PostgreSQL backup/restore rehearsal",
        "pg_dump",
        "pg_restore",
        "civiccode_restore_print_plan",
        "Compose project: civiccode_print_plan",
        "-p civiccode_print_plan",
        "civiccode-postgres.dump",
        "civiccode-docker-backup-manifest.json",
        "Drop the temporary restore database",
        "Fix path:",
        "DOCKER-BACKUP-RESTORE-REHEARSAL: PRINT-ONLY",
    ]:
        assert expected in result.stdout


def test_docker_backup_restore_rehearsal_helper_has_safe_restore_contract() -> None:
    script = (ROOT / "scripts" / "check_docker_backup_restore_rehearsal.py").read_text(
        encoding="utf-8"
    )

    assert "pg_dump" in script
    assert "pg_restore" in script
    assert "compose_project_name" in script
    assert "--compose-project-name" in script
    assert "DROP DATABASE IF EXISTS" in script
    assert "createdb" in script
    assert "table_schema NOT IN ('pg_catalog', 'information_schema')" in script
    assert "keep_restore_database" in script
    assert "restore_database_dropped" in script
    assert "civiccode-docker-backup-manifest.json" in script


def test_docker_backup_restore_rehearsal_powershell_wrapper_prints_expected_plan() -> None:
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if shell is None:
        pytest.skip("PowerShell runtime is not available in this environment.")

    result = subprocess.run(
        [
            shell,
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "start_docker_backup_restore_rehearsal.ps1"),
            "-PrintOnly",
            "-RunId",
            "print-plan",
            "-ComposeProjectName",
            "civiccode-print-plan",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for expected in [
        "CivicCode Docker/PostgreSQL backup/restore rehearsal profile",
        "Run id: print-plan",
        "Compose project: civiccode-print-plan",
        "Python verifier: python scripts/check_docker_backup_restore_rehearsal.py",
        "Backup dump: backup\\civiccode-postgres.dump",
        "Safety: the source civiccode database is not dropped or overwritten.",
        "Fix path:",
    ]:
        assert expected in result.stdout


def test_docker_backup_restore_rehearsal_wrappers_run_strict_by_default() -> None:
    powershell = (ROOT / "scripts" / "start_docker_backup_restore_rehearsal.ps1").read_text(
        encoding="utf-8"
    )
    bash = (ROOT / "scripts" / "start_docker_backup_restore_rehearsal.sh").read_text(
        encoding="utf-8"
    )

    assert '$ArgsList += "--strict"' in powershell
    assert "[switch]$Strict" not in powershell
    assert "strict=1" in bash
    assert "--strict)" not in bash


def test_docker_backup_restore_rehearsal_bash_wrapper_prints_expected_plan() -> None:
    shell = shutil.which("bash")
    if shell is None:
        pytest.skip("Bash runtime is not available in this environment.")

    result = subprocess.run(
        [
            shell,
            "scripts/start_docker_backup_restore_rehearsal.sh",
            "--print-only",
            "--run-id",
            "print-plan",
            "--compose-project-name",
            "civiccode-print-plan",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for expected in [
        "CivicCode Docker/PostgreSQL backup/restore rehearsal profile",
        "Run id: print-plan",
        "Compose project: civiccode-print-plan",
        "Python verifier: python scripts/check_docker_backup_restore_rehearsal.py",
        "Backup dump: backup/civiccode-postgres.dump",
        "Safety: the source civiccode database is not dropped or overwritten.",
        "Fix path:",
    ]:
        assert expected in result.stdout


def test_docs_reference_docker_backup_restore_rehearsal_helper() -> None:
    docs = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "README.txt").read_text(encoding="utf-8"),
            (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8"),
            (ROOT / "USER-MANUAL.txt").read_text(encoding="utf-8"),
            (ROOT / "docs" / "index.html").read_text(encoding="utf-8"),
            (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"),
        ]
    )

    for expected in [
        "scripts/start_docker_backup_restore_rehearsal.ps1",
        "scripts/start_docker_backup_restore_rehearsal.sh",
        "scripts/check_docker_backup_restore_rehearsal.py",
        ".docker-backup-restore-rehearsal",
        "civiccode-docker-backup-manifest.json",
        "pg_dump",
        "pg_restore",
    ]:
        assert expected in docs
