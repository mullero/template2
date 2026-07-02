-- =============================================================================
-- init-db.sql — Local Postgres bootstrap (mounted by docker-compose).
-- Idempotent: safe to run repeatedly. Schema/tables are owned by Alembic,
-- NOT by this file. This only prepares the database + extensions.
-- =============================================================================

-- Case-insensitive text + UUID helpers used by the app.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Ensure the public schema exists (default DB already has it).
CREATE SCHEMA IF NOT EXISTS public;
