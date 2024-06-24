"""add table

Revision ID: 18c2db25b26c
Revises: 19e7334216c9
Create Date: 2024-06-24 13:16:47.910256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18c2db25b26c'
down_revision = '19e7334216c9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cartitems', schema=None) as batch_op:
        batch_op.add_column(sa.Column('variation_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'product_variations', ['variation_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cartitems', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('variation_id')

    # ### end Alembic commands ###