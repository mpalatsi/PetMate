"""Add playdate photos table

Revision ID: add_playdate_photos_table
Revises: add_reviews_table
Create Date: 2023-11-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_playdate_photos_table'
down_revision = 'add_reviews_table'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('playdate_photo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('playdate_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('caption', sa.String(length=255), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['playdate_id'], ['playdate.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('playdate_photo') 