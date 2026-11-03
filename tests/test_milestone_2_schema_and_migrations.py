from __future__ import annotations

import ast
import importlib
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import ForeignKeyConstraint, create_engine, text


ROOT = Path(__file__).resolve().parents[1]

CANONICAL_TABLES = [
    "code_sources",
    "code_titles",
    "code_chapters",
    "code_sections",
    "section_versions",
    "section_citations",
    "interpretation_notes",
    "plain_language_summaries",
    "code_questions",
    "ordinance_events",
]

REQUIRED_COLUMNS = {
    "code_sources": {
        "id",
        "name",
        "publisher",
        "source_type",
        "source_category",
        "source_url",
        "file_reference",
        "retrieval_method",
        "retrieved_at",
        "checksum",
        "is_official",
        "status",
        "staff_notes",
        "metadata",
        "created_at",
        "updated_at",
    },
    "code_titles": {
        "id",
        "source_id",
        "title_number",
        "title_name",
        "sort_order",
        "created_at",
        "updated_at",
    },
    "code_chapters": {
        "id",
        "title_id",
        "chapter_number",
        "chapter_name",
        "sort_order",
        "created_at",
        "updated_at",
    },
    "code_sections": {
        "id",
        "chapter_id",
        "section_number",
        "section_heading",
        "parent_section_id",
        "sort_order",
        "created_at",
        "updated_at",
    },
    "section_versions": {
        "id",
        "section_id",
        "source_id",
        "version_label",
        "body",
        "effective_start",
        "effective_end",
        "adoption_event_id",
        "is_current",
        "created_at",
        "updated_at",
    },
    "section_citations": {
        "id",
        "section_version_id",
        "citation_text",
        "canonical_url",
        "retrieved_at",
        "created_at",
        "updated_at",
    },
    "interpretation_notes": {
        "id",
        "section_id",
        "note_text",
        "visibility",
        "status",
        "approved_by",
        "approved_at",
        "created_at",
        "updated_at",
    },
    "plain_language_summaries": {
        "id",
        "section_version_id",
        "summary_text",
        "status",
        "approved_by",
        "approved_at",
        "language_code",
        "created_at",
        "updated_at",
    },
    "code_questions": {
        "id",
        "question_text",
        "audience",
        "status",
        "answer_text",
        "citation_payload",
        "is_popular",
        "created_at",
        "updated_at",
    },
    "ordinance_events": {
        "id",
        "external_event_id",
        "townlight_meetings_meeting_id",
        "townlight_meetings_agenda_item_id",
        "ordinance_number",
        "title",
        "adopted_at",
        "affected_sections",
        "status",
        "source_document_url",
        "source_document_hash",
        "created_at",
        "updated_at",
    },
}

PLACEHOLDER_TARGET_PREFIXES = {
    "townlight_core.auth",
    "townlight_core.rbac",
    "townlight_core.audit",
    "townlight_core.ingestion",
    "townlight_core.search",
    "townlight_core.notifications",
    "townlight_core.connectors",
    "townlight_core.exemptions",
    "townlight_core.onboarding",
    "townlight_core.catalog",
    "townlight_core.verification",
}


def model_module():
    try:
        return importlib.import_module("townlight_code.models")
    except ModuleNotFoundError as exc:
        pytest.fail(f"townlight_code.models must exist for Milestone 2 schema work: {exc}")


def migration_path() -> Path:
    return ROOT / "townlight_code" / "migrations" / "versions" / "townlight_code_0001_schema.py"


def source_registry_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0002_source_registry_records.py"
    )


def popular_question_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0003_popular_question_records.py"
    )


def section_lifecycle_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0004_section_lifecycle_records.py"
    )


def staff_summary_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0005_staff_summary_records.py"
    )


def ordinance_handoff_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0006_ordinance_handoff_records.py"
    )


def import_job_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0007_import_job_records.py"
    )


def codifier_sync_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0008_codifier_sync.py"
    )


def operational_state_records_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0009_operational_state.py"
    )


def handoff_resolution_migration_path() -> Path:
    return (
        ROOT
        / "townlight_code"
        / "migrations"
        / "versions"
        / "townlight_code_0010_handoff_resolution.py"
    )


def test_canonical_table_models_exist_and_no_tables_are_missing_or_extra() -> None:
    models = model_module()
    metadata = models.Base.metadata
    townlight_code_tables = {
        key
        for key, table in metadata.tables.items()
        if table.schema == "townlight_code"
    }

    assert sorted(townlight_code_tables) == sorted(f"townlight_code.{name}" for name in CANONICAL_TABLES)


def test_models_use_townlight_code_schema_and_townlight_core_shared_base() -> None:
    models = model_module()
    townlight_core_db = importlib.import_module("townlight_core.db")

    assert models.Base is townlight_core_db.Base
    for table_name in CANONICAL_TABLES:
        table = models.Base.metadata.tables[f"townlight_code.{table_name}"]
        assert table.schema == "townlight_code"


def test_models_do_not_declare_a_competing_sqlalchemy_base() -> None:
    model_files = list((ROOT / "townlight_code").glob("**/*.py"))
    offenders: list[str] = []
    for path in model_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if getattr(base, "id", None) == "DeclarativeBase":
                        offenders.append(str(path.relative_to(ROOT)))
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "declarative_base":
                offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_each_canonical_table_has_required_foundation_columns() -> None:
    models = model_module()

    for table_name, expected_columns in REQUIRED_COLUMNS.items():
        table = models.Base.metadata.tables[f"townlight_code.{table_name}"]
        assert expected_columns <= set(table.columns.keys()), table_name


def test_no_foreign_keys_target_townlight_core_placeholder_packages_or_unreleased_shared_tables() -> None:
    models = model_module()

    for table in models.Base.metadata.tables.values():
        for constraint in table.constraints:
            if not isinstance(constraint, ForeignKeyConstraint):
                continue
            for element in constraint.elements:
                target = str(element.target_fullname)
                assert not any(target.startswith(prefix) for prefix in PLACEHOLDER_TARGET_PREFIXES)
                assert not target.startswith("townlight_core."), (
                    "TownlightCode may only FK into released TownlightCore tables; "
                    f"unexpected target: {target}"
                )


def test_alembic_scaffold_exists_for_townlight_code_schema_chain() -> None:
    expected = [
        ROOT / "townlight_code" / "migrations" / "alembic.ini",
        ROOT / "townlight_code" / "migrations" / "env.py",
        migration_path(),
        source_registry_records_migration_path(),
        popular_question_records_migration_path(),
        section_lifecycle_records_migration_path(),
        staff_summary_records_migration_path(),
        ordinance_handoff_records_migration_path(),
        import_job_records_migration_path(),
        codifier_sync_records_migration_path(),
        operational_state_records_migration_path(),
        handoff_resolution_migration_path(),
    ]

    for path in expected:
        assert path.exists(), f"Missing migration scaffold file: {path.relative_to(ROOT)}"


def test_alembic_env_runs_townlight_core_baseline_first_and_uses_separate_version_table() -> None:
    env_py = ROOT / "townlight_code" / "migrations" / "env.py"
    assert env_py.exists(), "townlight_code migrations env.py must exist."
    text = env_py.read_text(encoding="utf-8")

    assert "townlight_core.migrations.runner" in text
    assert "upgrade_to_head" in text
    assert "_database_url()" in text
    assert "_run_townlight_core_migrations(section[\"sqlalchemy.url\"])" in text
    assert "subprocess.run" in text
    assert "version_table=\"alembic_version_townlight_code\"" in text
    assert "target_metadata = Base.metadata" in text


def test_schema_aware_guard_checks_table_inside_target_schema() -> None:
    guard_py = ROOT / "townlight_code" / "migrations" / "guards.py"
    text = guard_py.read_text(encoding="utf-8")

    assert "schema = kwargs.get(\"schema\")" in text
    assert "has_table(name, schema=schema)" in text


def test_alembic_command_upgrades_real_pgvector_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the actual operator migration path against disposable Postgres."""
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI is not available for the real pgvector migration smoke.")
    daemon = subprocess.run(
        ["docker", "info"],
        check=False,
        capture_output=True,
        text=True,
    )
    if daemon.returncode != 0:
        pytest.skip(
            "Docker daemon is not available for the real pgvector migration smoke. "
            "Start Docker Desktop and rerun this test before release if Docker proof is required."
        )

    name = f"townlight_code-m2-{uuid.uuid4().hex[:12]}"
    subprocess.run(
        [
            "docker",
            "run",
            "--name",
            name,
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-e",
            "POSTGRES_USER=postgres",
            "-e",
            "POSTGRES_DB=townlight_code_test",
            "-p",
            "5432",
            "-d",
            "pgvector/pgvector:pg17",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    try:
        mapped = subprocess.run(
            ["docker", "port", name, "5432/tcp"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        port = mapped.rsplit(":", maxsplit=1)[-1]
        db_url = f"postgresql+psycopg2://postgres:postgres@localhost:{port}/townlight_code_test"
        engine = create_engine(db_url)

        deadline = time.monotonic() + 30
        while True:
            try:
                with engine.connect() as connection:
                    connection.execute(text("select 1"))
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)

        monkeypatch.setenv("DATABASE_URL", db_url)
        cfg = Config(str(ROOT / "townlight_code" / "migrations" / "alembic.ini"))

        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")

        with engine.connect() as connection:
            townlight_core_revision = connection.execute(
                text("select version_num from alembic_version_townlight_core")
            ).scalar_one()
            townlight_code_revision = connection.execute(
                text("select version_num from alembic_version_townlight_code")
            ).scalar_one()
            townlight_code_tables = set(
                connection.execute(
                    text(
                        """
                        select table_name
                        from information_schema.tables
                        where table_schema = 'townlight_code'
                        """
                    )
                ).scalars()
            )

        assert townlight_core_revision == "townlight_core_0009"
        assert townlight_code_revision == "townlight_code_0012"
        assert townlight_code_tables == set(CANONICAL_TABLES) | {
            "source_registry_records",
            "popular_question_records",
            "code_title_records",
            "code_chapter_records",
            "code_section_records",
            "section_version_records",
            "staff_interpretation_note_records",
            "staff_workbench_audit_event_records",
            "plain_language_summary_records",
            "plain_language_summary_audit_event_records",
            "ordinance_handoff_records",
            "ordinance_handoff_audit_event_records",
            "import_job_records",
            "codifier_sync_source_records",
            "codifier_sync_delta_plan_records",
            "operational_state_records",
        }
    finally:
        subprocess.run(["docker", "rm", "-f", name], check=False, capture_output=True, text=True)


def test_first_migration_declares_revision_and_creates_all_canonical_tables_idempotently() -> None:
    assert migration_path().exists(), "townlight_code_0001_schema migration must exist."
    text = migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0001"' in text
    assert "down_revision = None" in text
    assert "idempotent_create_table" in text
    assert 'op.execute("CREATE SCHEMA IF NOT EXISTS townlight_code")' in text

    for table_name in CANONICAL_TABLES:
        assert f'"{table_name}"' in text or f"'{table_name}'" in text
        assert 'schema="townlight_code"' in text or "schema='townlight_code'" in text


def test_migration_table_list_matches_model_metadata() -> None:
    models = model_module()
    text = migration_path().read_text(encoding="utf-8")

    model_tables = {
        table.name
        for table in models.Base.metadata.tables.values()
        if table.schema == "townlight_code"
    }
    for table_name in model_tables:
        assert f'"{table_name}"' in text or f"'{table_name}'" in text


def test_source_registry_records_migration_declares_persistent_records_table() -> None:
    text = source_registry_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0002"' in text
    assert 'down_revision = "townlight_code_0001"' in text
    assert "idempotent_create_table" in text
    assert '"source_registry_records"' in text
    assert '"source_id"' in text
    assert '"official_status_note"' in text
    assert 'schema="townlight_code"' in text


def test_popular_question_records_migration_declares_persistent_records_table() -> None:
    text = popular_question_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0003"' in text
    assert 'down_revision = "townlight_code_0002"' in text
    assert "idempotent_create_table" in text
    assert '"popular_question_records"' in text
    assert '"question_id"' in text
    assert '"section_number"' in text
    assert '"citation_payload"' in text
    assert 'schema="townlight_code"' in text


def test_section_lifecycle_records_migration_declares_persistent_records_tables() -> None:
    text = section_lifecycle_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0004"' in text
    assert 'down_revision = "townlight_code_0003"' in text
    assert "idempotent_create_table" in text
    for table_name in [
        "code_title_records",
        "code_chapter_records",
        "code_section_records",
        "section_version_records",
    ]:
        assert f'"{table_name}"' in text
    assert '"section_number"' in text
    assert '"effective_start"' in text
    assert 'schema="townlight_code"' in text


def test_staff_summary_records_migration_declares_persistent_records_tables() -> None:
    text = staff_summary_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0005"' in text
    assert 'down_revision = "townlight_code_0004"' in text
    assert "idempotent_create_table" in text
    for table_name in [
        "staff_interpretation_note_records",
        "staff_workbench_audit_event_records",
        "plain_language_summary_records",
        "plain_language_summary_audit_event_records",
    ]:
        assert f'"{table_name}"' in text
    assert '"summary_text"' in text
    assert '"approved_by"' in text
    assert 'schema="townlight_code"' in text


def test_ordinance_handoff_records_migration_declares_persistent_records_tables() -> None:
    text = ordinance_handoff_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0006"' in text
    assert 'down_revision = "townlight_code_0005"' in text
    assert "idempotent_create_table" in text
    for table_name in [
        "ordinance_handoff_records",
        "ordinance_handoff_audit_event_records",
    ]:
        assert f'"{table_name}"' in text
    assert '"townlight_meetings_meeting_id"' in text
    assert '"affected_sections"' in text
    assert 'schema="townlight_code"' in text


def test_import_job_records_migration_declares_persistent_records_table() -> None:
    text = import_job_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0007"' in text
    assert 'down_revision = "townlight_code_0006"' in text
    assert "idempotent_create_table" in text
    assert '"import_job_records"' in text
    assert '"job_id"' in text
    assert '"provenance"' in text
    assert '"failure"' in text
    assert 'schema="townlight_code"' in text


def test_codifier_sync_records_migration_declares_persistent_records_tables() -> None:
    text = codifier_sync_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0008"' in text
    assert 'down_revision = "townlight_code_0007"' in text
    assert "idempotent_create_table" in text
    for table_name in [
        "codifier_sync_source_records",
        "codifier_sync_delta_plan_records",
    ]:
        assert f'"{table_name}"' in text
    assert '"host_validation"' in text
    assert '"next_sync_at"' in text
    assert '"sync_paused"' in text


def test_operational_state_records_migration_declares_persistent_records_table() -> None:
    text = operational_state_records_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0009"' in text
    assert 'down_revision = "townlight_code_0008"' in text
    assert "idempotent_create_table" in text
    assert '"operational_state_records"' in text
    for column_name in [
        "record_type",
        "subject_id",
        "next_attempt_at",
        "cursor_key",
        "cursor_value",
        "replay_of",
        "payload_hash",
    ]:
        assert f'"{column_name}"' in text


def test_handoff_resolution_migration_declares_durable_resolution_fields() -> None:
    text = handoff_resolution_migration_path().read_text(encoding="utf-8")

    assert 'revision = "townlight_code_0010"' in text
    assert 'down_revision = "townlight_code_0009"' in text
    for column_name in [
        "resolved_section_version_id",
        "resolved_by",
        "resolved_at",
    ]:
        assert column_name in text


def test_migration_revision_ids_fit_alembic_version_column() -> None:
    """Alembic's default version table stores revision IDs in VARCHAR(32)."""
    migrations_dir = ROOT / "townlight_code" / "migrations" / "versions"
    for migration in migrations_dir.glob("*.py"):
        text = migration.read_text(encoding="utf-8")
        match = re.search(r'^revision = "([^"]+)"', text, flags=re.MULTILINE)
        if match is None:
            continue
        revision = match.group(1)
        assert len(revision) <= 32, f"{migration.name} revision ID is too long: {revision}"


def test_docs_and_changelog_record_schema_milestone_without_claiming_code_answers_historical_edition() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").lower()
    manual = (ROOT / "docs" / "history" / "pre-townlight-beta-1" / "USER-MANUAL.md").read_text(encoding="utf-8").lower()
    landing = (ROOT / "docs" / "history" / "pre-townlight-beta-1" / "docs" / "index.html").read_text(encoding="utf-8").lower()

    for document_text in [changelog, manual, landing]:
        assert "canonical schema" in document_text
        assert "alembic" in document_text
        assert "code answers are available" not in document_text
