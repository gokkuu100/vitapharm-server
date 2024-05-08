"""categories in products

Revision ID: 90589d1167b2
Revises: ce6eaacd041a
Create Date: 2024-04-23 10:40:25.403684

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '90589d1167b2'
down_revision = 'ce6eaacd041a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('data',
               existing_type=mysql.MEDIUMBLOB(),
               type_=sa.LargeBinary(length=16277215),
               existing_nullable=True)

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('town', sa.String(length=24), nullable=False))
        batch_op.add_column(sa.Column('phone', sa.String(length=30), nullable=False))
        batch_op.drop_column('city')

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('sub_category', sa.String(length=64), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('sub_category')
        batch_op.drop_column('category')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('city', mysql.VARCHAR(length=24), nullable=False))
        batch_op.drop_column('phone')
        batch_op.drop_column('town')

    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('data',
               existing_type=sa.LargeBinary(length=16277215),
               type_=mysql.MEDIUMBLOB(),
               existing_nullable=True)

    # ### end Alembic commands ###