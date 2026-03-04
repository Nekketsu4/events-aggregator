"""Update eventstatus enum

Revision ID: 67d3f76be244
Revises: 311e42519119
Create Date: 2026-03-04 19:17:29.387514

"""

from typing import Sequence, Union

from alembic import op

revision: str = "67d3f76be244"
down_revision: Union[str, Sequence[str], None] = "311e42519119"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE eventstatus RENAME VALUE 'new' TO 'registration_closed'")
    # ### end Alembic commands ###

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TYPE eventstatus RENAME VALUE 'registration_closed' TO 'new'")
    # ### end Alembic commands ###