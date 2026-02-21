"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-02-04 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'ABANDONED', name='sessionstatus'), nullable=False),
        sa.Column('patient_info', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', 'SYSTEM', name='messagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_index(op.f('ix_messages_session_id'), 'messages', ['session_id'], unique=False)

    # Create diagnostic_results table
    op.create_table(
        'diagnostic_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('assessment_json', sa.JSON(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_diagnostic_results_id'), 'diagnostic_results', ['id'], unique=False)
    op.create_index(op.f('ix_diagnostic_results_session_id'), 'diagnostic_results', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_diagnostic_results_session_id'), table_name='diagnostic_results')
    op.drop_index(op.f('ix_diagnostic_results_id'), table_name='diagnostic_results')
    op.drop_table('diagnostic_results')
    
    op.drop_index(op.f('ix_messages_session_id'), table_name='messages')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
    
    op.execute('DROP TYPE sessionstatus')
    op.execute('DROP TYPE messagerole')
