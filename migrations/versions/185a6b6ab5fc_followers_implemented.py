"""followers implemented

Revision ID: 185a6b6ab5fc
Revises: 6d0a3783ff8e
Create Date: 2021-02-24 20:26:29.512937

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '185a6b6ab5fc'
down_revision = '6d0a3783ff8e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
