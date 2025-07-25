-- Auto_RFP Database Schema (Simplified for Azure PostgreSQL constraints)
-- This creates tables without requiring extensions or schema creation privileges
-- Uses built-in UUID generation instead of uuid-ossp extension

-- Users table
CREATE TABLE IF NOT EXISTS auto_rfp_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table
CREATE TABLE IF NOT EXISTS auto_rfp_organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- LlamaCloud integration fields
    llama_cloud_project_id VARCHAR(255),
    llama_cloud_project_name VARCHAR(255),
    llama_cloud_org_name VARCHAR(255),
    llama_cloud_connected_at TIMESTAMP WITH TIME ZONE
);

-- Organization Users (many-to-many relationship)
CREATE TABLE IF NOT EXISTS auto_rfp_organization_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auto_rfp_users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES auto_rfp_organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, organization_id)
);

-- Projects table
CREATE TABLE IF NOT EXISTS auto_rfp_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID NOT NULL REFERENCES auto_rfp_organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS auto_rfp_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    project_id UUID NOT NULL REFERENCES auto_rfp_projects(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'processed', 'error'))
);

-- Questions table
CREATE TABLE IF NOT EXISTS auto_rfp_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_id VARCHAR(255),
    text TEXT NOT NULL,
    topic VARCHAR(255) NOT NULL,
    section_title VARCHAR(255),
    project_id UUID NOT NULL REFERENCES auto_rfp_projects(id) ON DELETE CASCADE,
    document_id UUID REFERENCES auto_rfp_documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Answers table
CREATE TABLE IF NOT EXISTS auto_rfp_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES auto_rfp_questions(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sources table (for answer citations)
CREATE TABLE IF NOT EXISTS auto_rfp_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    answer_id UUID NOT NULL REFERENCES auto_rfp_answers(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT,
    page_number VARCHAR(50),
    document_id UUID REFERENCES auto_rfp_documents(id) ON DELETE SET NULL,
    relevance INTEGER CHECK (relevance >= 0 AND relevance <= 100),
    text_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Project Indexes (LlamaCloud integration)
CREATE TABLE IF NOT EXISTS auto_rfp_project_indexes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES auto_rfp_projects(id) ON DELETE CASCADE,
    index_id VARCHAR(255) NOT NULL,
    index_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, index_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_auto_rfp_organizations_slug ON auto_rfp_organizations(slug);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_organization_users_user ON auto_rfp_organization_users(user_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_organization_users_org ON auto_rfp_organization_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_projects_org ON auto_rfp_projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_documents_project ON auto_rfp_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_questions_project ON auto_rfp_questions(project_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_questions_document ON auto_rfp_questions(document_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_answers_question ON auto_rfp_answers(question_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_sources_answer ON auto_rfp_sources(answer_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_project_indexes_project ON auto_rfp_project_indexes(project_id);