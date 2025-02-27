"""Add reviews table

Revision ID: add_reviews_table
Revises: add_pet_owner_fields
Create Date: 2023-11-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_reviews_table'
down_revision = 'add_pet_owner_fields'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('review',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reviewer_id', sa.Integer(), nullable=False),
        sa.Column('reviewed_user_id', sa.Integer(), nullable=False),
        sa.Column('playdate_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['playdate_id'], ['playdate.id'], ),
        sa.ForeignKeyConstraint(['reviewed_user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['reviewer_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('review') 