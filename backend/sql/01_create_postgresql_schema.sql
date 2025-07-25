-- Auto_RFP PostgreSQL Database Schema
-- This creates all necessary tables for the RFP automation platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- LlamaCloud integration fields
    llama_cloud_project_id VARCHAR(255),
    llama_cloud_project_name VARCHAR(255),
    llama_cloud_org_name VARCHAR(255),
    llama_cloud_connected_at TIMESTAMP WITH TIME ZONE
);

-- Organization Users (many-to-many relationship with roles)
CREATE TABLE IF NOT EXISTS organization_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, organization_id)
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(100) NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'processed', 'error'))
);

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reference_id VARCHAR(50),
    text TEXT NOT NULL,
    topic VARCHAR(255) NOT NULL,
    section_title VARCHAR(255),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Answers table
CREATE TABLE IF NOT EXISTS answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sources table (for answer citations)
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    page_number VARCHAR(20),
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    relevance INTEGER CHECK (relevance >= 0 AND relevance <= 100),
    text_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project Indexes (LlamaCloud integration)
CREATE TABLE IF NOT EXISTS project_indexes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    index_id VARCHAR(255) NOT NULL,
    index_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, index_id)
);

-- Enhanced tables for additional features

-- User profiles with authentication data
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    avatar_url VARCHAR(500),
    bio TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API Keys for external integrations
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NOT NULL, -- 'openai', 'azure', 'llamacloud', etc.
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project Templates
CREATE TABLE IF NOT EXISTS project_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- 'government', 'enterprise', 'consulting', etc.
    template_data JSONB, -- JSON with default questions, sections, etc.
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID NOT NULL REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE UNIQUE,
    page_count INTEGER,
    language VARCHAR(10) DEFAULT 'en',
    ocr_confidence DECIMAL(3,2),
    processing_time_seconds DECIMAL(8,2),
    azure_doc_intelligence_model VARCHAR(100),
    extraction_method VARCHAR(50), -- 'azure_di', 'llamaparse', 'manual'
    content_hash VARCHAR(64), -- SHA256 hash of content
    tags JSONB, -- JSON array of tags
    metadata JSONB, -- JSON field for additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Question metadata with categorization
CREATE TABLE IF NOT EXISTS question_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE UNIQUE,
    complexity VARCHAR(10) CHECK (complexity IN ('low', 'medium', 'high')),
    category VARCHAR(50), -- 'technical', 'commercial', 'administrative', 'legal'
    priority INTEGER DEFAULT 0, -- 0-100 priority score
    estimated_words INTEGER, -- Expected answer length
    keywords JSONB, -- JSON array of extracted keywords
    section_number VARCHAR(20), -- e.g., "2.3.1"
    page_number INTEGER,
    is_required BOOLEAN DEFAULT TRUE,
    extraction_confidence DECIMAL(3,2),
    metadata JSONB, -- JSON field for additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Answer versions for workflow management
CREATE TABLE IF NOT EXISTS answer_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.0,
    generation_method VARCHAR(20), -- 'ai_generated', 'human_written', 'hybrid'
    model_used VARCHAR(100), -- e.g., 'gpt-4', 'azure-openai'
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'rejected')),
    created_by UUID REFERENCES users(id),
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    word_count INTEGER,
    processing_time_seconds DECIMAL(8,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(answer_id, version_number)
);

-- Source metadata for better citation tracking
CREATE TABLE IF NOT EXISTS source_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE UNIQUE,
    embedding_vector TEXT, -- Serialized vector for similarity search
    chunk_index INTEGER, -- Position in document chunks
    similarity_score DECIMAL(5,4), -- Similarity to question
    extraction_method VARCHAR(50), -- 'vector_search', 'keyword_match', 'manual'
    context_before TEXT, -- Text before the source
    context_after TEXT, -- Text after the source
    bounding_box JSONB, -- JSON with coordinates if available
    metadata JSONB, -- JSON field for additional metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Activity logging for audit trail
CREATE TABLE IF NOT EXISTS activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    project_id UUID REFERENCES projects(id),
    action_type VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'view', 'generate'
    resource_type VARCHAR(50) NOT NULL, -- 'document', 'question', 'answer', 'project'
    resource_id UUID NOT NULL,
    details JSONB, -- JSON with action details
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Export/Import tracking
CREATE TABLE IF NOT EXISTS export_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id),
    export_type VARCHAR(20) NOT NULL, -- 'pdf', 'docx', 'json', 'csv'
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    file_path VARCHAR(500),
    parameters JSONB, -- JSON with export parameters
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- AI Model configurations per organization
CREATE TABLE IF NOT EXISTS ai_model_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    model_name VARCHAR(100) NOT NULL, -- 'gpt-4', 'gpt-3.5-turbo', etc.
    model_type VARCHAR(20) NOT NULL, -- 'chat', 'embedding', 'completion'
    endpoint_url VARCHAR(500),
    api_version VARCHAR(20),
    deployment_name VARCHAR(100),
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.3,
    system_prompt TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vector search collections tracking
CREATE TABLE IF NOT EXISTS vector_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    collection_name VARCHAR(255) NOT NULL,
    vector_dimension INTEGER NOT NULL,
    distance_metric VARCHAR(20) DEFAULT 'cosine',
    indexed_documents INTEGER DEFAULT 0,
    total_vectors INTEGER DEFAULT 0,
    last_indexed_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB, -- JSON with collection configuration
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, collection_name)
);

-- Performance metrics tracking
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    project_id UUID REFERENCES projects(id),
    metric_type VARCHAR(50) NOT NULL, -- 'response_time', 'accuracy', 'user_satisfaction'
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(20), -- 'seconds', 'percentage', 'count'
    dimensions JSONB, -- JSON with additional dimensions
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);
CREATE INDEX IF NOT EXISTS idx_organization_users_user ON organization_users(user_id);
CREATE INDEX IF NOT EXISTS idx_organization_users_org ON organization_users(organization_id);
CREATE INDEX IF NOT EXISTS idx_projects_org ON projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_questions_project ON questions(project_id);
CREATE INDEX IF NOT EXISTS idx_questions_document ON questions(document_id);
CREATE INDEX IF NOT EXISTS idx_answers_question ON answers(question_id);
CREATE INDEX IF NOT EXISTS idx_sources_answer ON sources(answer_id);
CREATE INDEX IF NOT EXISTS idx_project_indexes_project ON project_indexes(project_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_service ON api_keys(service_type);
CREATE INDEX IF NOT EXISTS idx_document_metadata_doc ON document_metadata(document_id);
CREATE INDEX IF NOT EXISTS idx_question_metadata_question ON question_metadata(question_id);
CREATE INDEX IF NOT EXISTS idx_question_metadata_category ON question_metadata(category);
CREATE INDEX IF NOT EXISTS idx_answer_versions_answer ON answer_versions(answer_id);
CREATE INDEX IF NOT EXISTS idx_answer_versions_status ON answer_versions(status);
CREATE INDEX IF NOT EXISTS idx_source_metadata_source ON source_metadata(source_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_user ON activity_log(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_org ON activity_log(organization_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_project ON activity_log(project_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_created ON activity_log(created_at);
CREATE INDEX IF NOT EXISTS idx_export_jobs_project ON export_jobs(project_id);
CREATE INDEX IF NOT EXISTS idx_export_jobs_user ON export_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_export_jobs_status ON export_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ai_model_configs_org ON ai_model_configs(organization_id);
CREATE INDEX IF NOT EXISTS idx_vector_collections_org ON vector_collections(organization_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_org ON performance_metrics(organization_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_project ON performance_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_measured ON performance_metrics(measured_at);

-- Create views for common queries
CREATE OR REPLACE VIEW project_summary AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.organization_id,
    o.name as organization_name,
    COUNT(DISTINCT d.id) as document_count,
    COUNT(DISTINCT q.id) as question_count,
    COUNT(DISTINCT a.id) as answer_count,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT q.id) > 0 
            THEN (COUNT(DISTINCT a.id)::decimal / COUNT(DISTINCT q.id) * 100)
            ELSE 0 
        END, 1
    ) as completion_percentage,
    p.created_at,
    p.updated_at
FROM projects p
JOIN organizations o ON p.organization_id = o.id
LEFT JOIN documents d ON p.id = d.project_id
LEFT JOIN questions q ON p.id = q.project_id
LEFT JOIN answers a ON q.id = a.question_id
GROUP BY p.id, p.name, p.description, p.organization_id, o.name, p.created_at, p.updated_at;

CREATE OR REPLACE VIEW organization_stats AS
SELECT 
    o.id,
    o.name,
    o.slug,
    COUNT(DISTINCT p.id) as project_count,
    COUNT(DISTINCT ou.user_id) as member_count,
    COUNT(DISTINCT d.id) as total_documents,
    COUNT(DISTINCT q.id) as total_questions,
    COUNT(DISTINCT a.id) as total_answers,
    o.created_at,
    o.updated_at
FROM organizations o
LEFT JOIN projects p ON o.id = p.organization_id
LEFT JOIN organization_users ou ON o.id = ou.organization_id
LEFT JOIN documents d ON p.id = d.project_id
LEFT JOIN questions q ON p.id = q.project_id
LEFT JOIN answers a ON q.id = a.question_id
GROUP BY o.id, o.name, o.slug, o.created_at, o.updated_at;