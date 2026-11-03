"""Schema-aware idempotent Alembic helpers for TownlightCode migrations."""

from __future__ import annotations

from typing import Any

import alembic.op as op
import sqlalchemy as sa
from sqlalchemy.engine import Inspector


def _inspector() -> Inspector:
    return sa.inspect(op.get_bind())


def idempotent_create_table(name: str, *columns: Any, **kwargs: Any) -> None:
    """Create a table unless it already exists in the requested schema."""
    schema = kwargs.get("schema")
    if _inspector().has_table(name, schema=schema):
        return
    op.create_table(name, *columns, **kwargs)
