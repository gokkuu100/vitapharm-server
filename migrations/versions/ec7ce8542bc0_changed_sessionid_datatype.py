"""changed sessionid datatype

Revision ID: ec7ce8542bc0
Revises: 7bfe7429c48e
Create Date: 2024-04-03 21:38:22.385485

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ec7ce8542bc0'
down_revision = '7bfe7429c48e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cart', schema=None) as batch_op:
        batch_op.alter_column('session_id',
               existing_type=mysql.INTEGER(),
               type_=sa.String(length=128),
               existing_nullable=True)

    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('data',
               existing_type=mysql.MEDIUMBLOB(),
               type_=sa.LargeBinary(length=16277215),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('data',
               existing_type=sa.LargeBinary(length=16277215),
               type_=mysql.MEDIUMBLOB(),
               existing_nullable=True)

    with op.batch_alter_table('cart', schema=None) as batch_op:
        batch_op.alter_column('session_id',
               existing_type=sa.String(length=128),
               type_=mysql.INTEGER(),
               existing_nullable=True)

    # ### end Alembic commands ###