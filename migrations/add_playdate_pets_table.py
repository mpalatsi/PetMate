"""Add playdate_pets association table

Revision ID: add_playdate_pets
Revises: previous_revision_id
Create Date: 2023-10-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_playdate_pets'
down_revision = None  # Replace with the previous migration ID if you have one
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('playdate_pets',
        sa.Column('playdate_id', sa.Integer(), nullable=False),
        sa.Column('pet_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['pet_id'], ['pet.id'], ),
        sa.ForeignKeyConstraint(['playdate_id'], ['playdate.id'], ),
        sa.PrimaryKeyConstraint('playdate_id', 'pet_id')
    )

def downgrade():
    op.drop_table('playdate_pets') 