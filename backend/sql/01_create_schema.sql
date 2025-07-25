-- Create Auto_RFP Schema (safe - won't affect existing data)
-- This creates a separate namespace for all Auto_RFP tables

CREATE SCHEMA IF NOT EXISTS auto_rfp;

-- Set search path to include our schema
-- Users can still access other schemas explicitly with schema.table syntax