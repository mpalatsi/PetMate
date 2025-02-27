"""Add gallery photos table

Revision ID: add_gallery_photos_table
Revises: add_playdate_photos_table
Create Date: 2023-11-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_gallery_photos_table'
down_revision = 'add_playdate_photos_table'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('gallery_photo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('pet_id', sa.Integer(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('likes', sa.Integer(), nullable=True, default=0),
        sa.Column('is_public', sa.Boolean(), nullable=True, default=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pet_id'], ['pet.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('gallery_photo') 