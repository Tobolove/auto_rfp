from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class QuestionComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    MULTI_PART = "multi-part"

class StepType(str, Enum):
    ANALYZE_QUESTION = "analyze_question"
    SEARCH_DOCUMENTS = "search_documents"
    EXTRACT_INFORMATION = "extract_information"
    SYNTHESIZE_RESPONSE = "synthesize_response"
    VALIDATE_ANSWER = "validate_answer"

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

# User Models
class User(BaseModel):
    """User model for authentication and organization membership."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    email: str
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None

# Organization Models
class Organization(BaseModel):
    """Represents an organization or a tenant in the system."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # LlamaCloud integration
    llama_cloud_project_id: Optional[str] = None
    llama_cloud_project_name: Optional[str] = None
    llama_cloud_org_name: Optional[str] = None
    llama_cloud_connected_at: Optional[datetime] = None

class OrganizationCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class OrganizationUser(BaseModel):
    """Represents the relationship between users and organizations."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    organization_id: UUID
    role: UserRole = UserRole.MEMBER
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Project Models
class Project(BaseModel):
    """Represents an RFP project within an organization."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    organization_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: UUID

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

# Document Models
class Document(BaseModel):
    """Represents an uploaded RFP document."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    original_name: str
    file_path: str
    file_size: int
    file_type: str
    project_id: UUID
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: str = "uploaded"  # uploaded, processing, processed, error

class DocumentCreate(BaseModel):
    name: str
    original_name: str
    file_path: str
    file_size: int
    file_type: str
    project_id: UUID

# Question and Answer Models
class Question(BaseModel):
    """Represents a question extracted from an RFP document."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    reference_id: Optional[str] = None  # AI-generated ID like "question_1.10.1"
    text: str
    topic: str
    section_title: Optional[str] = None
    project_id: UUID
    document_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class QuestionCreate(BaseModel):
    reference_id: Optional[str] = None
    text: str
    topic: str
    section_title: Optional[str] = None
    project_id: UUID
    document_id: Optional[UUID] = None

class Section(BaseModel):
    """Represents a section containing multiple questions."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: Optional[str] = None
    questions: List[Question] = []

class Answer(BaseModel):
    """Represents an AI-generated answer to a question."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    question_id: UUID
    text: str
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class AnswerCreate(BaseModel):
    question_id: UUID
    text: str
    confidence: float = 0.0

class Source(BaseModel):
    """Represents a source document for an answer."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    answer_id: UUID
    file_name: str
    file_path: Optional[str] = None
    page_number: Optional[str] = None
    document_id: Optional[str] = None
    relevance: Optional[int] = None
    text_content: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class SourceCreate(BaseModel):
    answer_id: UUID
    file_name: str
    file_path: Optional[str] = None
    page_number: Optional[str] = None
    document_id: Optional[str] = None
    relevance: Optional[int] = None
    text_content: Optional[str] = None

class SourceData(BaseModel):
    """Source data without answer_id for initial creation."""
    file_name: str
    file_path: Optional[str] = None
    page_number: Optional[str] = None
    document_id: Optional[str] = None
    relevance: Optional[int] = None
    text_content: Optional[str] = None

# AI Processing Models
class QuestionAnalysis(BaseModel):
    """Analysis result for a question."""
    complexity: QuestionComplexity
    required_information: List[str]
    specific_entities: List[str]
    search_queries: List[str]
    expected_sources: int
    reasoning: str

class DocumentSearchResult(BaseModel):
    """Search result from document analysis."""
    query: str
    documents_found: int
    relevant_sources: List[Dict[str, Any]]
    coverage: str  # complete, partial, insufficient

class StepResult(BaseModel):
    """Result of a processing step."""
    id: str
    type: StepType
    title: str
    description: str
    status: StepStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MultiStepResponse(BaseModel):
    """Multi-step AI response generation result."""
    id: str
    question_id: UUID
    project_id: UUID
    steps: List[StepResult]
    final_response: str
    overall_confidence: float
    total_duration: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# Request/Response Models
class ExtractQuestionsRequest(BaseModel):
    document_id: Union[str, UUID]
    project_id: Union[str, UUID]
    
    @field_validator('document_id', 'project_id')
    @classmethod
    def validate_uuid(cls, v):
        if isinstance(v, str):
            try:
                return UUID(v)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {v}")
        return v

class ExtractQuestionsResponse(BaseModel):
    document_id: UUID
    project_id: UUID
    total_questions: int
    sections: List[Section]
    processing_time: float
    extraction_method: str

class GenerateResponseRequest(BaseModel):
    question: str
    question_id: UUID
    project_id: UUID
    index_ids: List[str] = []
    context: Optional[str] = None
    use_all_indexes: bool = False

class GenerateResponseResponse(BaseModel):
    success: bool
    response: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]

# LlamaCloud Models
class LlamaCloudProject(BaseModel):
    """LlamaCloud project information."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class LlamaCloudConnectRequest(BaseModel):
    organization_id: UUID
    project_id: str
    project_name: str
    llama_cloud_org_name: Optional[str] = None

class ProjectIndex(BaseModel):
    """Project index for LlamaCloud integration."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    index_id: str  # LlamaCloud pipeline ID
    index_name: str  # LlamaCloud pipeline name
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
