"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-08-30 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    user_status_enum = sa.Enum('active', 'inactive', 'suspended', 'pending_verification', name='user_status')
    user_status_enum.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('status', user_status_enum, nullable=False, server_default='pending_verification'),
        sa.Column('roles', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('permissions', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        schema='freestack'
    )

    op.create_index('ix_users_email', 'users', ['email'], schema='freestack')
    op.create_index('ix_users_username', 'users', ['username'], schema='freestack')
    op.create_index('ix_users_email_status', 'users', ['email', 'status'], schema='freestack')
    op.create_index('ix_users_username_status', 'users', ['username', 'status'], schema='freestack')

    # User sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('freestack.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False, unique=True),
        sa.Column('refresh_token', sa.String(255), nullable=False, unique=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('revoked', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='freestack'
    )

    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'], schema='freestack')
    op.create_index('ix_user_sessions_session_token', 'user_sessions', ['session_token'], schema='freestack')
    op.create_index('ix_user_sessions_refresh_token', 'user_sessions', ['refresh_token'], schema='freestack')
    op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'], schema='freestack')
    op.create_index('ix_user_sessions_user_expires', 'user_sessions', ['user_id', 'expires_at'], schema='freestack')

    # API keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('freestack.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('permissions', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean, nullable=False, server_default='false'),
        schema='freestack'
    )

    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], schema='freestack')
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], schema='freestack')
    op.create_index('ix_api_keys_user_deleted', 'api_keys', ['user_id', 'is_deleted'], schema='freestack')
    op.create_unique_constraint('uq_api_keys_user_name', 'api_keys', ['user_id', 'name'], schema='freestack')

    # Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('freestack.users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('request_id', sa.String(50), nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('success', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='freestack'
    )

    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], schema='freestack')
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], schema='freestack')
    op.create_index('ix_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], schema='freestack')
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], schema='freestack')
    op.create_index('ix_audit_logs_request_id', 'audit_logs', ['request_id'], schema='freestack')

    # Create updated_at trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION freestack.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add triggers for updated_at
    op.execute("""
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON freestack.users
        FOR EACH ROW EXECUTE FUNCTION freestack.update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_user_sessions_updated_at
        BEFORE UPDATE ON freestack.user_sessions
        FOR EACH ROW EXECUTE FUNCTION freestack.update_updated_at_column();
    """)

    op.execute("""
        CREATE TRIGGER update_api_keys_updated_at
        BEFORE UPDATE ON freestack.api_keys
        FOR EACH ROW EXECUTE FUNCTION freestack.update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_users_updated_at ON freestack.users')
    op.execute('DROP TRIGGER IF EXISTS update_user_sessions_updated_at ON freestack.user_sessions')
    op.execute('DROP TRIGGER IF EXISTS update_api_keys_updated_at ON freestack.api_keys')
    op.execute('DROP FUNCTION IF EXISTS freestack.update_updated_at_column()')

    # Drop tables
    op.drop_table('audit_logs', schema='freestack')
    op.drop_table('api_keys', schema='freestack')
    op.drop_table('user_sessions', schema='freestack')
    op.drop_table('users', schema='freestack')

    # Drop enum
    user_status_enum = sa.Enum('active', 'inactive', 'suspended', 'pending_verification', name='user_status')
    user_status_enum.drop(op.get_bind(), checkfirst=True)