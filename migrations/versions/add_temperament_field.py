"""Add temperament field to Pet model

Revision ID: add_temperament_field
Revises: 
Create Date: 2023-07-05 12:34:56.789012

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_temperament_field'
down_revision = None  # Replace with the ID of the previous migration if needed
branch_labels = None
depends_on = None


def upgrade():
    # Add temperament column to the pets table
    op.add_column('pets', sa.Column('temperament', sa.Text(), nullable=True))


def downgrade():
    # Remove temperament column from the pets table
    op.drop_column('pets', 'temperament') 