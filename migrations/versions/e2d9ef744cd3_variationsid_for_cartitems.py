"""variationsId for cartitems

Revision ID: e2d9ef744cd3
Revises: ff22ad0ff9db
Create Date: 2024-06-23 11:18:29.920727

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'e2d9ef744cd3'
down_revision = 'ff22ad0ff9db'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [column['name'] for column in inspector.get_columns('cartitems')]

    if 'variation_id' not in columns:
        with op.batch_alter_table('cartitems') as batch_op:
            batch_op.add_column(sa.Column('variation_id', sa.Integer))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cartitems', schema=None) as batch_op:
        batch_op.add_column(sa.Column('product_variation_id', mysql.INTEGER(), autoincrement=False, nullable=True))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('cartitems_ibfk_2', 'product_variations', ['product_variation_id'], ['id'])
        batch_op.drop_column('variation_id')

    # ### end Alembic commands ###