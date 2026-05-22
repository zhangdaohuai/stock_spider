import json
import os
from logging.config import fileConfig

from typing import Any

from alembic import context  # type: ignore[import-untyped]

config = context.config

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except (KeyError, ValueError):
        pass


def _build_database_url() -> str:
    config_path = os.environ.get(
        "CONFIG_PATH",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "db_config.json"),
    )
    with open(config_path, encoding="utf-8") as f:
        db_cfg: dict[str, Any] = json.load(f)

    host = str(db_cfg["host"])
    port = int(db_cfg["port"])
    database = str(db_cfg["database"])
    user = str(db_cfg["user"])
    password_env_key = str(db_cfg["password_env"])
    password = os.environ.get(password_env_key, "")

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


config.set_main_option("sqlalchemy.url", _build_database_url())

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import engine_from_config
    from sqlalchemy import pool

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
