"""
Reference Document Models for Qdrant Vector Store Integration
"""
from typing import List, Optional, Dict, Any
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of reference documents that can be uploaded."""
    COMPANY_PROFILE = "company_profile"
    CASE_STUDY = "case_study"
    TECHNICAL_SPECS = "technical_specs"
    CERTIFICATIONS = "certifications"
    TEAM_BIOS = "team_bios"
    PRICING_TEMPLATES = "pricing_templates"
    METHODOLOGY = "methodology"
    PARTNERSHIPS = "partnerships"
    AWARDS = "awards"
    OTHER = "other"


class IndustryTag(str, Enum):
    """Industry classification tags."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    GOVERNMENT = "government"
    EDUCATION = "education"
    RETAIL = "retail"
    ENERGY = "energy"
    TELECOMMUNICATIONS = "telecommunications"
    AUTOMOTIVE = "automotive"
    AEROSPACE = "aerospace"
    OTHER = "other"


class CapabilityTag(str, Enum):
    """Technical capability tags."""
    CLOUD_MIGRATION = "cloud_migration"
    DATA_ANALYTICS = "data_analytics"
    CYBERSECURITY = "cybersecurity"
    AI_ML = "ai_ml"
    INTEGRATION = "integration"
    MOBILE_DEVELOPMENT = "mobile_development"
    WEB_DEVELOPMENT = "web_development"
    DATABASE_MANAGEMENT = "database_management"
    DEVOPS = "devops"
    CONSULTING = "consulting"
    PROJECT_MANAGEMENT = "project_management"
    QUALITY_ASSURANCE = "quality_assurance"
    UI_UX_DESIGN = "ui_ux_design"
    BLOCKCHAIN = "blockchain"
    IOT = "iot"
    OTHER = "other"


class ProjectSize(str, Enum):
    """Project size classifications."""
    SMALL = "small"          # < $100K
    MEDIUM = "medium"        # $100K - $500K
    LARGE = "large"          # $500K - $2M
    ENTERPRISE = "enterprise" # > $2M


class GeographicScope(str, Enum):
    """Geographic scope classifications."""
    LOCAL = "local"
    REGIONAL = "regional"
    NATIONAL = "national"
    INTERNATIONAL = "international"


class ConfidenceLevel(str, Enum):
    """Confidence level for document relevance."""
    HIGH = "high"      # Always use for relevant questions
    MEDIUM = "medium"  # Use with moderate relevance
    LOW = "low"        # Use only when highly relevant


class ReferenceDocumentMetadata(BaseModel):
    """Metadata structure for reference documents in Qdrant."""
    document_id: str = Field(default_factory=lambda: str(uuid4()))
    filename: str
    original_name: str
    document_type: DocumentType
    industry_tags: List[IndustryTag] = Field(default_factory=list)
    capability_tags: List[CapabilityTag] = Field(default_factory=list)
    project_size: Optional[ProjectSize] = None
    geographic_scope: Optional[GeographicScope] = None
    organization_id: str
    upload_date: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    custom_tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ReferenceDocumentCreate(BaseModel):
    """Request model for creating reference documents."""
    filename: str
    original_name: str
    document_type: DocumentType
    industry_tags: List[IndustryTag] = Field(default_factory=list)
    capability_tags: List[CapabilityTag] = Field(default_factory=list)
    project_size: Optional[ProjectSize] = None
    geographic_scope: Optional[GeographicScope] = None
    organization_id: str
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    custom_tags: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class ReferenceDocumentUpdate(BaseModel):
    """Request model for updating reference document metadata."""
    document_type: Optional[DocumentType] = None
    industry_tags: Optional[List[IndustryTag]] = None
    capability_tags: Optional[List[CapabilityTag]] = None
    project_size: Optional[ProjectSize] = None
    geographic_scope: Optional[GeographicScope] = None
    confidence_level: Optional[ConfidenceLevel] = None
    custom_tags: Optional[List[str]] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ReferenceDocumentFilter(BaseModel):
    """Filter model for searching reference documents."""
    document_types: Optional[List[DocumentType]] = None
    industry_tags: Optional[List[IndustryTag]] = None
    capability_tags: Optional[List[CapabilityTag]] = None
    project_sizes: Optional[List[ProjectSize]] = None
    geographic_scopes: Optional[List[GeographicScope]] = None
    confidence_levels: Optional[List[ConfidenceLevel]] = None
    is_active: bool = True
    keywords: Optional[List[str]] = None


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    file_content: bytes
    metadata: ReferenceDocumentCreate


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    success: bool
    document_id: str
    message: str
    metadata: Optional[ReferenceDocumentMetadata] = None
    vector_id: Optional[str] = None


class SmartFilterRequest(BaseModel):
    """Request for AI-powered document filtering based on RFP question."""
    question: str
    organization_id: str
    context: Optional[str] = None  # Additional context about the RFP
    max_documents: int = Field(default=10, ge=1, le=50)


class SmartFilterResponse(BaseModel):
    """Response with intelligently filtered documents."""
    success: bool
    filters_applied: ReferenceDocumentFilter
    reasoning: str  # Explanation of why these filters were chosen
    estimated_relevance: float  # 0.0 to 1.0
    recommended_document_types: List[DocumentType]