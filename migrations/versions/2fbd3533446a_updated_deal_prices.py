"""updated deal prices

Revision ID: 2fbd3533446a
Revises: b2795c4f864e
Create Date: 2024-04-23 19:27:28.250143

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '2fbd3533446a'
down_revision = 'b2795c4f864e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('data',
               existing_type=mysql.MEDIUMBLOB(),
               type_=sa.LargeBinary(length=16277215),
               existing_nullable=True)

    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deal_price', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('deal_start_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('deal_end_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('deal_end_time')
        batch_op.drop_column('deal_start_time')
        batch_op.drop_column('deal_price')

    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('data',
               existing_type=sa.LargeBinary(length=16277215),
               type_=mysql.MEDIUMBLOB(),
               existing_nullable=True)

    # ### end Alembic commands ###
