-- Auto_RFP Database Schema
-- This creates all necessary tables in the auto_rfp schema
-- SAFE: Will not affect any existing tables in other schemas

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS auto_rfp.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table
CREATE TABLE IF NOT EXISTS auto_rfp.organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
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
CREATE TABLE IF NOT EXISTS auto_rfp.organization_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auto_rfp.users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES auto_rfp.organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, organization_id)
);

-- Projects table
CREATE TABLE IF NOT EXISTS auto_rfp.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID NOT NULL REFERENCES auto_rfp.organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE IF NOT EXISTS auto_rfp.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    project_id UUID NOT NULL REFERENCES auto_rfp.projects(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'processed', 'error'))
);

-- Questions table
CREATE TABLE IF NOT EXISTS auto_rfp.questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_id VARCHAR(255),
    text TEXT NOT NULL,
    topic VARCHAR(255) NOT NULL,
    section_title VARCHAR(255),
    project_id UUID NOT NULL REFERENCES auto_rfp.projects(id) ON DELETE CASCADE,
    document_id UUID REFERENCES auto_rfp.documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Answers table
CREATE TABLE IF NOT EXISTS auto_rfp.answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES auto_rfp.questions(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sources table (for answer citations)
CREATE TABLE IF NOT EXISTS auto_rfp.sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID NOT NULL REFERENCES auto_rfp.answers(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT,
    page_number VARCHAR(50),
    document_id UUID REFERENCES auto_rfp.documents(id) ON DELETE SET NULL,
    relevance INTEGER CHECK (relevance >= 0 AND relevance <= 100),
    text_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Project Indexes (LlamaCloud integration)
CREATE TABLE IF NOT EXISTS auto_rfp.project_indexes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES auto_rfp.projects(id) ON DELETE CASCADE,
    index_id VARCHAR(255) NOT NULL,
    index_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, index_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_auto_rfp_organizations_slug ON auto_rfp.organizations(slug);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_organization_users_user ON auto_rfp.organization_users(user_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_organization_users_org ON auto_rfp.organization_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_projects_org ON auto_rfp.projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_documents_project ON auto_rfp.documents(project_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_questions_project ON auto_rfp.questions(project_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_questions_document ON auto_rfp.questions(document_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_answers_question ON auto_rfp.answers(question_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_sources_answer ON auto_rfp.sources(answer_id);
CREATE INDEX IF NOT EXISTS idx_auto_rfp_project_indexes_project ON auto_rfp.project_indexes(project_id);