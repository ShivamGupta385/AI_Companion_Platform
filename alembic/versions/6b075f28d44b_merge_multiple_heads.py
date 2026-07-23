"""merge multiple heads

Revision ID: 6b075f28d44b
Revises: 23de61df1a8f, 52ad84b0589c
Create Date: 2026-07-17 16:24:00.001361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b075f28d44b'
down_revision: Union[str, Sequence[str], None] = ('23de61df1a8f', '52ad84b0589c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
