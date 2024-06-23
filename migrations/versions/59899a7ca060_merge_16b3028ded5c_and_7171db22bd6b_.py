"""merge 16b3028ded5c and 7171db22bd6b heads

Revision ID: 59899a7ca060
Revises: 
Create Date: 2024-06-23 20:57:11.852223

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59899a7ca060'
down_revision = ('16b3028ded5c', '7171db22bd6b')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
