"""rename authorization description columns

Revision ID: c7a1b9e5d4f2
Revises: b2f4c7d9a1e0
Create Date: 2026-06-19 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


revision: str = "c7a1b9e5d4f2"
down_revision: Union[str, Sequence[str], None] = "b2f4c7d9a1e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _rename_column(table_name: str, old_name: str, new_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.alter_column(old_name, new_column_name=new_name)


def upgrade() -> None:
    """Upgrade schema."""
    _rename_column("permissions", "descpription", "description")
    _rename_column("roles", "descpription", "description")


def downgrade() -> None:
    """Downgrade schema."""
    _rename_column("roles", "description", "descpription")
    _rename_column("permissions", "description", "descpription")
