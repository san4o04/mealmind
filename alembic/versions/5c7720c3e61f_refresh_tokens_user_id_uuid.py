"""refresh_tokens user_id uuid

Revision ID: 5c7720c3e61f
Revises: bae270b21de8
Create Date: 2025-12-17 22:44:15.075514

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # если таблица пустая: просто меняем колонку
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "user_id")
    op.add_column(
        "refresh_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "user_id")
    op.add_column(
        "refresh_tokens",
        sa.Column("user_id", sa.Integer(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


# revision identifiers, used by Alembic.
revision: str = '5c7720c3e61f'
down_revision: Union[str, Sequence[str], None] = 'bae270b21de8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
