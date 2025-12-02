"""add_ai_features_column

Revision ID: 8d914a794ef0
Revises: 97d32aa4e203
Create Date: 2025-12-02 16:36:09.546809

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8d914a794ef0'
down_revision = '97d32aa4e203'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ai_features column as ARRAY(String)
    op.add_column('products', sa.Column('ai_features', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    # Remove ai_features column
    op.drop_column('products', 'ai_features')

