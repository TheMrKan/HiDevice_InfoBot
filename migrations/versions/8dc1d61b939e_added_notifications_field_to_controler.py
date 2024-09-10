"""Added 'notifications' field to Controler

Revision ID: 8dc1d61b939e
Revises: 5566e5969f09
Create Date: 2024-09-10 17:19:14.908146

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dc1d61b939e'
down_revision: Union[str, None] = '5566e5969f09'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('controllers', sa.Column('notifications', sa.Integer(), server_default='0', nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('controllers', 'notifications')
    # ### end Alembic commands ###