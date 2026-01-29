-- Initial database setup for WellnessWay Diet Planner
-- This file will be executed when the PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create initial database structure (tables will be created via Alembic migrations)
-- This file is mainly for extensions and initial setup

-- Set timezone
SET timezone = 'UTC';

-- Create a function to generate UUIDs (alternative to uuid-ossp)
-- This ensures UUID generation works even if uuid-ossp is not available
CREATE OR REPLACE FUNCTION gen_random_uuid() RETURNS uuid AS $$
BEGIN
    RETURN uuid_generate_v4();
EXCEPTION WHEN undefined_function THEN
    -- Fallback to a simple UUID generation if uuid_generate_v4 is not available
    RETURN (SELECT md5(random()::text || clock_timestamp()::text)::uuid);
END;
$$ LANGUAGE plpgsql;