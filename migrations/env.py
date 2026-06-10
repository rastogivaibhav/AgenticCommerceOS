from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _database_url() -> str:
    url = os.environ.get("ACOS_NORTHSTAR_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL or ACOS_NORTHSTAR_DATABASE_URL is required for Alembic migrations")
    if url.startswith("postgresql+psycopg://"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    engine = create_engine(_database_url(), pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
