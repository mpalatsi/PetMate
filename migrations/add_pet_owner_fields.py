"""Add pet owner fields to User model

Revision ID: add_pet_owner_fields
Revises: add_playdate_pets
Create Date: 2023-10-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_pet_owner_fields'
down_revision = 'add_playdate_pets'  # This should match your previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to the user table
    op.add_column('user', sa.Column('preferred_meetup_types', sa.String(255), nullable=True))
    op.add_column('user', sa.Column('availability', sa.String(255), nullable=True))
    op.add_column('user', sa.Column('pet_owner_since', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('pet_experience_level', sa.String(50), nullable=True))

def downgrade():
    # Remove columns if needed to rollback
    op.drop_column('user', 'preferred_meetup_types')
    op.drop_column('user', 'availability')
    op.drop_column('user', 'pet_owner_since')
    op.drop_column('user', 'pet_experience_level') 