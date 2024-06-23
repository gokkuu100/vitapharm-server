"""dummy migration to bridge gap

Revision ID: 69865ee43833
Revises: ff22ad0ff9db
Create Date: 2024-06-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '69865ee43833'
down_revision = 'e2d9ef744cd3'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
