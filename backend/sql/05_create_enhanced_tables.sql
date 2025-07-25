-- Enhanced Auto_RFP Database Schema with additional features
-- This extends the basic schema with advanced features

-- Enhanced Users table with authentication
CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    avatar_url TEXT,
    bio TEXT,
    timezone TEXT DEFAULT 'UTC',
    preferences TEXT, -- JSON field for user preferences
    last_login_at DATETIME,
    login_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- API Keys for external integrations
CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    service_type TEXT NOT NULL, -- 'openai', 'azure', 'llamacloud', etc.
    encrypted_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at DATETIME,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Project Templates
CREATE TABLE IF NOT EXISTS project_templates (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT, -- 'government', 'enterprise', 'consulting', etc.
    template_data TEXT, -- JSON with default questions, sections, etc.
    is_public BOOLEAN DEFAULT FALSE,
    created_by TEXT NOT NULL REFERENCES users(id),
    organization_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Documents with metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_count INTEGER,
    language TEXT DEFAULT 'en',
    ocr_confidence REAL,
    processing_time_seconds REAL,
    azure_doc_intelligence_model TEXT,
    extraction_method TEXT, -- 'azure_di', 'llamaparse', 'manual'
    content_hash TEXT, -- SHA256 hash of content
    tags TEXT, -- JSON array of tags
    metadata TEXT, -- JSON field for additional metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id)
);

-- Enhanced Questions with categorization and complexity
CREATE TABLE IF NOT EXISTS question_metadata (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    complexity TEXT CHECK (complexity IN ('low', 'medium', 'high')),
    category TEXT, -- 'technical', 'commercial', 'administrative', 'legal'
    priority INTEGER DEFAULT 0, -- 0-100 priority score
    estimated_words INTEGER, -- Expected answer length
    keywords TEXT, -- JSON array of extracted keywords
    section_number TEXT, -- e.g., "2.3.1"
    page_number INTEGER,
    is_required BOOLEAN DEFAULT TRUE,
    extraction_confidence REAL,
    metadata TEXT, -- JSON field for additional metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id)
);

-- Enhanced Answers with versioning and approval workflow
CREATE TABLE IF NOT EXISTS answer_versions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    answer_id TEXT NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    text TEXT NOT NULL,
    confidence REAL DEFAULT 0.0,
    generation_method TEXT, -- 'ai_generated', 'human_written', 'hybrid'
    model_used TEXT, -- e.g., 'gpt-4', 'azure-openai'
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'rejected')),
    created_by TEXT REFERENCES users(id),
    reviewed_by TEXT REFERENCES users(id),
    review_notes TEXT,
    word_count INTEGER,
    processing_time_seconds REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(answer_id, version_number)
);

-- Source metadata for better citation tracking
CREATE TABLE IF NOT EXISTS source_metadata (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    embedding_vector TEXT, -- Serialized vector for similarity search
    chunk_index INTEGER, -- Position in document chunks
    similarity_score REAL, -- Similarity to question
    extraction_method TEXT, -- 'vector_search', 'keyword_match', 'manual'
    context_before TEXT, -- Text before the source
    context_after TEXT, -- Text after the source
    bounding_box TEXT, -- JSON with coordinates if available
    metadata TEXT, -- JSON field for additional metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_id)
);

-- Activity logging for audit trail
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    user_id TEXT REFERENCES users(id),
    organization_id TEXT REFERENCES organizations(id),
    project_id TEXT REFERENCES projects(id),
    action_type TEXT NOT NULL, -- 'create', 'update', 'delete', 'view', 'generate'
    resource_type TEXT NOT NULL, -- 'document', 'question', 'answer', 'project'
    resource_id TEXT NOT NULL,
    details TEXT, -- JSON with action details
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Export/Import tracking
CREATE TABLE IF NOT EXISTS export_jobs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id),
    export_type TEXT NOT NULL, -- 'pdf', 'docx', 'json', 'csv'
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    file_path TEXT,
    parameters TEXT, -- JSON with export parameters
    progress_percentage INTEGER DEFAULT 0,
    error_message TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- AI Model configurations per organization
CREATE TABLE IF NOT EXISTS ai_model_configs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL, -- 'gpt-4', 'gpt-3.5-turbo', etc.
    model_type TEXT NOT NULL, -- 'chat', 'embedding', 'completion'
    endpoint_url TEXT,
    api_version TEXT,
    deployment_name TEXT,
    max_tokens INTEGER DEFAULT 4000,
    temperature REAL DEFAULT 0.3,
    system_prompt TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Vector search collections tracking
CREATE TABLE IF NOT EXISTS vector_collections (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    organization_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    collection_name TEXT NOT NULL,
    vector_dimension INTEGER NOT NULL,
    distance_metric TEXT DEFAULT 'cosine',
    indexed_documents INTEGER DEFAULT 0,
    total_vectors INTEGER DEFAULT 0,
    last_indexed_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    metadata TEXT, -- JSON with collection configuration
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, collection_name)
);

-- Performance metrics tracking
CREATE TABLE IF NOT EXISTS performance_metrics (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    organization_id TEXT REFERENCES organizations(id),
    project_id TEXT REFERENCES projects(id),
    metric_type TEXT NOT NULL, -- 'response_time', 'accuracy', 'user_satisfaction'
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    metric_unit TEXT, -- 'seconds', 'percentage', 'count'
    dimensions TEXT, -- JSON with additional dimensions
    measured_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create additional indexes for performance
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
CREATE VIEW IF NOT EXISTS project_summary AS
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
            THEN (COUNT(DISTINCT a.id) * 100.0 / COUNT(DISTINCT q.id))
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

CREATE VIEW IF NOT EXISTS organization_stats AS
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