"""build and mapped file table

Revision ID: 71267b4386b8
Revises: 8777317a403d
Create Date: 2025-04-19 03:58:41.655259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71267b4386b8'
down_revision: Union[str, None] = '8777317a403d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('file',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('upload_date', sa.DateTime(), nullable=False),
    sa.Column('size', sa.BigInteger(), nullable=False),
    sa.Column('s3_url', sa.String(), nullable=False),
    sa.Column('owner_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_filename'), 'file', ['filename'], unique=False)
    op.create_index(op.f('ix_file_s3_url'), 'file', ['s3_url'], unique=True)
    op.create_index(op.f('ix_file_upload_date'), 'file', ['upload_date'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_file_upload_date'), table_name='file')
    op.drop_index(op.f('ix_file_s3_url'), table_name='file')
    op.drop_index(op.f('ix_file_filename'), table_name='file')
    op.drop_table('file')
    # ### end Alembic commands ###
