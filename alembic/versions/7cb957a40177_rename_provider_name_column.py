"""rename provider name column

Revision ID: 7cb957a40177
Revises: 5f4e525fe81f
Create Date: 2026-09-08 08:20:44.704237

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7cb957a40177'
down_revision: Union[str, Sequence[str], None] = '5f4e525fe81f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('providers', 'name', new_column_name='provider_name')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('providers', 'provider_name', new_column_name='name')
