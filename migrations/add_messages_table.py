"""Add messages table

Revision ID: add_messages_table
Revises: add_pet_owner_fields
Create Date: 2023-10-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_messages_table'
down_revision = 'add_pet_owner_fields'  # This should match your previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Create messages table
    op.create_table('message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Drop messages table
    op.drop_table('message') 