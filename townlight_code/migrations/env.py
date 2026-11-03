from __future__ import annotations

from logging.config import fileConfig
import os
import subprocess
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

from townlight_code.models import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Resolve the one database URL used by both TownlightCore and TownlightCode."""
    url = config.get_main_option("sqlalchemy.url") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "TownlightCode migrations require a database URL. Set DATABASE_URL or "
            "set sqlalchemy.url on the Alembic Config before running upgrade."
        )
    return url


def _run_townlight_core_migrations(url: str) -> None:
    """Run TownlightCore first without nesting Alembic EnvironmentContext proxies."""
    env = os.environ.copy()
    env["DATABASE_URL"] = url
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from townlight_core.migrations.runner import upgrade_to_head; upgrade_to_head()",
        ],
        env=env,
        check=True,
    )


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_townlight_code",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _run_townlight_core_migrations(section["sqlalchemy.url"])
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version_townlight_code",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
