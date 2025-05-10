"""change attribute name s3_url to access_url

Revision ID: 1c8388bbce4c
Revises: cc25977df0a8
Create Date: 2025-05-09 22:02:13.647156

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1c8388bbce4c"
down_revision: Union[str, None] = "cc25977df0a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.alter_column("file", "s3_url", new_column_name="access_url")
    op.drop_index("ix_file_s3_url", table_name="file")
    op.create_index(op.f("ix_file_access_url"), "file", ["access_url"], unique=True)


def downgrade():
    op.alter_column("file", "access_url", new_column_name="s3_url")
    op.drop_index(op.f("ix_file_access_url"), table_name="file")
    op.create_index("ix_file_s3_url", "file", ["s3_url"], unique=True)
