from logging.config import fileConfig
import os
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv


# 1) Make sure project root is on PYTHONPATH (Windows + Alembic fix)
sys.path.append(str(Path(__file__).resolve().parents[1]))

# 2) Load .env before reading DATABASE_URL
load_dotenv()

# Alembic Config object
config = context.config

# 3) Set sqlalchemy.url from .env BEFORE creating engine / running migrations
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is not set in .env")
config.set_main_option("sqlalchemy.url", database_url)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 4) Import Base + models so autogenerate can see metadata
from app.db.base import Base  # noqa: E402
from app.models.refresh_token import RefreshToken  # noqa: F401, E402

# IMPORTANT: User model import must match your real file/module name.
# If you don't have app/models/user.py, change this import or delete it.


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
