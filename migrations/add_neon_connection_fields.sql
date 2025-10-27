-- Migration: Add Neon PostgreSQL connection fields to project_metadata
-- Purpose: Store dedicated Neon project connection strings for each webapp
-- This enables persistence across restarts and allows conversation resumption

-- Add Neon connection fields
ALTER TABLE project_metadata
ADD COLUMN IF NOT EXISTS neon_project_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS neon_database_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS neon_database_url_pooled VARCHAR(500),
ADD COLUMN IF NOT EXISTS neon_region VARCHAR(50),
ADD COLUMN IF NOT EXISTS neon_branch_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS neon_database_name VARCHAR(100);

-- Add index for Neon project ID lookups
CREATE INDEX IF NOT EXISTS idx_project_neon_id ON project_metadata(neon_project_id);

-- Add comment
COMMENT ON COLUMN project_metadata.neon_project_id IS 'Neon project ID (e.g., ep-cool-meadow-123456)';
COMMENT ON COLUMN project_metadata.neon_database_url IS 'Regular Neon connection string for migrations';
COMMENT ON COLUMN project_metadata.neon_database_url_pooled IS 'Pooled Neon connection string for serverless functions';
COMMENT ON COLUMN project_metadata.neon_region IS 'Neon region (e.g., aws-us-east-1)';
COMMENT ON COLUMN project_metadata.neon_branch_id IS 'Neon branch ID (e.g., br-main-xyz)';
COMMENT ON COLUMN project_metadata.neon_database_name IS 'Neon database name (e.g., neondb)';
