"""add_person

Revision ID: 05055a834cf3
Revises: 8e985bfba90a
Create Date: 2025-04-05 02:50:27.845315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05055a834cf3'
down_revision: Union[str, None] = '8e985bfba90a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('persons',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('map_id', sa.Integer(), nullable=False),
    sa.Column('target_product', sa.String(), nullable=True),
    sa.Column('preferences', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('history_coordinates', sa.JSON(), server_default='[]', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default='now()', nullable=False),
    sa.ForeignKeyConstraint(['map_id'], ['maps.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_persons_id'), 'persons', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_persons_id'), table_name='persons')
    op.drop_table('persons')
    # ### end Alembic commands ###
