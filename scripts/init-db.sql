-- FreeStack Database Initialization Script
-- Run this script to initialize the database with required extensions and settings

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS freestack;

-- Set search path
ALTER DATABASE freestack SET search_path TO freestack, public;

-- Create custom types
DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended', 'pending_verification');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('superadmin', 'admin', 'manager', 'user', 'viewer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Create indexes for common queries (will be created by Alembic migrations)
-- This script just ensures the database is ready for migrations

-- Set timezone
SET timezone = 'UTC';

-- Configure connection settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE freestack TO freestack;
GRANT ALL PRIVILEGES ON SCHEMA freestack TO freestack;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA freestack TO freestack;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA freestack TO freestack;

-- Create read-only role for reporting
CREATE ROLE freestack_readonly;
GRANT CONNECT ON DATABASE freestack TO freestack_readonly;
GRANT USAGE ON SCHEMA freestack TO freestack_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA freestack TO freestack_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA freestack GRANT SELECT ON TABLES TO freestack_readonly;