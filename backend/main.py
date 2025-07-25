import os
# Configure Python path for imports
import config_path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Database configuration
from database_config import connect_db, disconnect_db

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID
import asyncio
from datetime import datetime

from models import (
    # Organization models
    Organization, OrganizationCreate, OrganizationUpdate,
    User, UserCreate, OrganizationUser, UserRole,
    # Project models  
    Project, ProjectCreate, ProjectUpdate,
    Document, DocumentCreate,
    Question, QuestionCreate, Section,
    Answer, AnswerCreate, Source, SourceCreate, SourceData,
    # AI models
    ExtractQuestionsRequest, ExtractQuestionsResponse,
    GenerateResponseRequest, GenerateResponseResponse,
    MultiStepResponse,
    # LlamaCloud models
    LlamaCloudConnectRequest, ProjectIndex
)

# Reference document models
from models_reference import (
    ReferenceDocumentMetadata, ReferenceDocumentCreate, ReferenceDocumentUpdate,
    ReferenceDocumentFilter, DocumentUploadRequest, DocumentUploadResponse,
    SmartFilterRequest, SmartFilterResponse
)

from services.organization_service import organization_service
from services.project_service import project_service
from services.ai_service import ai_service
from services.document_service import document_service
from services.question_extraction_service import question_extraction_service
from services.qdrant_service import qdrant_service
from services.response_generation_service import response_generation_service
from services.reference_document_service import reference_document_service
# Temporarily disable Qdrant imports to fix startup
# from services.qdrant_service_factory import get_qdrant_service, initialize_quote_collection, test_qdrant_connection

app = FastAPI(
    title="AutoRFP Backend API",
    description="Comprehensive API for the AutoRFP platform - AI-powered RFP response automation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],  # Angular and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure AI service with API keys from environment
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    print("Starting AutoRFP Backend API...")
    
    # Connect to database
    await connect_db()
    
    # Verify database connection
    from database_config import database
    print(f"FastAPI startup - Database connected: {database.is_connected}")
    
    # Configure AI service
    openai_key = os.getenv("OPENAI_API_KEY")
    llamacloud_key = os.getenv("LLAMACLOUD_API_KEY")
    
    if openai_key:
        ai_service.configure(openai_api_key=openai_key)
        print("OpenAI API configured")
    if llamacloud_key:
        ai_service.configure(llamacloud_api_key=llamacloud_key)
        print("LlamaCloud API configured")
    
    # Skip Qdrant initialization for now to avoid blocking startup
    print("Skipping Qdrant initialization (can be done later)")
    
    print("AutoRFP Backend API startup completed!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    await disconnect_db()
    print("AutoRFP Backend API shutdown completed!")

# Health check and root endpoint
@app.get("/")
async def root():
    """Root endpoint to check if the API is running."""
    # Test Qdrant connection for health status
    qdrant_status = "disabled"  # Temporarily disabled
    # try:
    #     qdrant_service = get_qdrant_service()
    #     collections = qdrant_service.qdrant_client.get_collections()
    #     qdrant_status = "connected"
    # except:
    #     qdrant_status = "disconnected"
    
    return {
        "message": "Welcome to the AutoRFP Backend API!",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "qdrant_vector_db": qdrant_status
        }
    }

@app.get("/debug/database")
async def debug_database():
    """Debug database connection and operations."""
    from database_config import database, get_table_name
    from services.organization_service import organization_service
    from models import OrganizationCreate, UserCreate
    
    try:
        org_table = get_table_name("organizations")
        rows = await database.fetch_all(f"SELECT COUNT(*) as count FROM {org_table}")
        count = rows[0]['count'] if rows else 0
        
        # Test organization creation directly
        test_user = await organization_service.get_user_by_email("debug@test.com")
        if not test_user:
            test_user = await organization_service.create_user(UserCreate(
                email="debug@test.com",
                name="Debug User"
            ))
        
        test_org = OrganizationCreate(
            name="Debug API Test",
            slug="debug-api-test",
            description="Direct API debug test"
        )
        
        created_org = await organization_service.create_organization(test_org, test_user.id)
        
        # Check count after creation
        rows2 = await database.fetch_all(f"SELECT COUNT(*) as count FROM {org_table}")
        count_after = rows2[0]['count'] if rows2 else 0
        
        return {
            "database_connected": database.is_connected,
            "organizations_count_before": count,
            "organizations_count_after": count_after,
            "created_org_id": str(created_org.id),
            "table_name": org_table
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "database_connected": getattr(database, 'is_connected', False)
        }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    # Check Qdrant health
    qdrant_health = "disabled"  # Temporarily disabled
    # try:
    #     qdrant_service = get_qdrant_service()
    #     collections = qdrant_service.qdrant_client.get_collections()
    #     qdrant_health = "healthy"
    # except Exception as e:
    #     qdrant_health = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "organization_service": "active",
            "project_service": "active", 
            "ai_service": "active",
            "qdrant_vector_db": qdrant_health
        }
    }

# === ORGANIZATION ENDPOINTS ===

@app.post("/organizations", response_model=Organization, status_code=201)
async def create_organization(
    name: str = Form(...),
    slug: str = Form(...), 
    description: Optional[str] = Form(None),
    owner_email: str = Form(...)
):
    """Create a new organization with the specified user as owner."""
    try:
        # Create OrganizationCreate model from form data
        organization = OrganizationCreate(
            name=name,
            slug=slug,
            description=description
        )
        
        # Get or create user
        user = await organization_service.get_user_by_email(owner_email)
        if not user:
            user = await organization_service.create_user(UserCreate(email=owner_email))
        
        # Create organization
        org = await organization_service.create_organization(organization, user.id)
        return org
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizations", response_model=List[Organization])
async def get_organizations(user_email: Optional[str] = None):
    """Get all organizations, optionally filtered by user membership."""
    try:
        user_id = None
        if user_email:
            user = await organization_service.get_user_by_email(user_email)
            if user:
                user_id = user.id
        
        organizations = await organization_service.get_organizations(user_id)
        return organizations
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizations/{org_id}", response_model=Organization)
async def get_organization(org_id: UUID, include_relations: bool = False):
    """Get organization by ID."""
    org = await organization_service.get_organization(org_id, include_relations)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.put("/organizations/{org_id}", response_model=Organization)
async def update_organization(org_id: UUID, update_data: OrganizationUpdate):
    """Update organization."""
    org = await organization_service.update_organization(org_id, update_data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.delete("/organizations/{org_id}")
async def delete_organization(org_id: UUID):
    """Delete organization and all related data."""
    success = await organization_service.delete_organization(org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization deleted successfully"}

# Organization membership endpoints
@app.post("/organizations/{org_id}/members")
async def add_member_to_organization(
    org_id: UUID,
    user_email: str = Form(...),
    role: UserRole = Form(UserRole.MEMBER)
):
    """Add a user to an organization."""
    try:
        # Get or create user
        user = await organization_service.get_user_by_email(user_email)
        if not user:
            user = await organization_service.create_user(UserCreate(email=user_email))
        
        # Add to organization
        org_user = await organization_service.add_user_to_organization(user.id, org_id, role)
        return {"message": "User added to organization successfully", "role": role}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizations/{org_id}/members")
async def get_organization_members(org_id: UUID):
    """Get all members of an organization."""
    members = await organization_service.get_organization_members(org_id)
    return {"members": members}

@app.put("/organizations/{org_id}/members/{user_id}/role")
async def update_member_role(org_id: UUID, user_id: UUID, new_role: UserRole = Form(...)):
    """Update a user's role in an organization."""
    result = await organization_service.update_user_role(user_id, org_id, new_role)
    if not result:
        raise HTTPException(status_code=404, detail="Organization membership not found")
    return {"message": "Role updated successfully", "new_role": new_role}

@app.delete("/organizations/{org_id}/members/{user_id}")
async def remove_member_from_organization(org_id: UUID, user_id: UUID):
    """Remove a user from an organization."""
    success = await organization_service.remove_user_from_organization(user_id, org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization membership not found")
    return {"message": "User removed from organization successfully"}

# === PROJECT ENDPOINTS ===

@app.post("/projects", response_model=Project, status_code=201)
async def create_project(project: ProjectCreate):
    """Create a new RFP project."""
    try:
        # Verify organization exists
        org = await organization_service.get_organization(project.organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        new_project = await project_service.create_project(project)
        return new_project
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects", response_model=List[Project])
async def get_projects(organization_id: Optional[UUID] = None):
    """Get all projects, optionally filtered by organization."""
    projects = await project_service.get_projects(organization_id)
    return projects

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: UUID, include_relations: bool = False):
    """Get project by ID."""
    project = await project_service.get_project(project_id, include_relations)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/projects/{project_id}", response_model=Project)
async def update_project(project_id: UUID, update_data: ProjectUpdate):
    """Update project."""
    project = await project_service.update_project(project_id, update_data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.delete("/projects/{project_id}")
async def delete_project(project_id: UUID):
    """Delete project and all related data."""
    success = await project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

@app.get("/projects/{project_id}/stats")
async def get_project_stats(project_id: UUID):
    """Get project statistics and analytics."""
    stats = await project_service.get_project_stats(project_id)
    return stats

# === DOCUMENT ENDPOINTS ===

@app.post("/projects/{project_id}/documents", response_model=Document, status_code=201)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """Upload a document to a project with AI processing."""
    try:
        # Verify project exists
        project = await project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Read file content
        file_content = await file.read()
        
        # Upload and process document using the document service
        document = await document_service.upload_document(
            file_content=file_content,
            filename=file.filename,
            project_id=str(project_id),
            content_type=file.content_type
        )
        
        return document
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/projects/{project_id}/documents", response_model=List[Document])
async def get_project_documents(project_id: UUID):
    """Get all documents for a project."""
    documents = await document_service.get_project_documents(str(project_id))
    return documents

@app.get("/documents/{document_id}", response_model=Document)
async def get_document(document_id: UUID):
    """Get document by ID."""
    document = await document_service.get_document(str(document_id))
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@app.put("/documents/{document_id}/status")
async def update_document_status(document_id: UUID, status: str = Form(...)):
    """Update document processing status."""
    document = await project_service.update_document_status(document_id, status)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document status updated", "status": status}

@app.delete("/documents/{document_id}")
async def delete_document(document_id: UUID):
    """Delete a document and its associated file."""
    try:
        success = await document_service.delete_document(str(document_id))
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

# === AI PROCESSING ENDPOINTS ===

@app.post("/ai/extract-questions", response_model=ExtractQuestionsResponse)
async def extract_questions_from_document(request: ExtractQuestionsRequest):
    """Extract questions from RFP document using AI."""
    try:
        print(f"DEBUG: Endpoint called with request: {request}")
        
        # Verify document exists
        document = await document_service.get_document(str(request.document_id))
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        print(f"DEBUG: Document found: {document.name}")
        
        # Extract questions using AI
        result = await question_extraction_service.extract_questions_from_document(request)
        
        print(f"DEBUG: Extraction completed, result type: {type(result)}")
        print(f"DEBUG: Result sections type: {type(result.sections) if hasattr(result, 'sections') else 'No sections'}")
        
        return result
    except Exception as e:
        print(f"DEBUG: Exception in endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/{project_id}/questions", response_model=List[Question])
async def get_project_questions(project_id: UUID):
    """Get all questions for a project."""
    questions = await question_extraction_service.get_project_questions(str(project_id))
    return questions

@app.post("/ai/generate-response", response_model=GenerateResponseResponse)
async def generate_ai_response(request: GenerateResponseRequest):
    """Generate AI response for a question using RAG."""
    try:
        print(f"DEBUG: Generate response endpoint called with request: {request}")
        
        # Use the new RAG-based answer service
        from services.rag_answer_service import rag_answer_service
        response = await rag_answer_service.generate_answer(request)
        
        print(f"DEBUG: RAG response generated successfully")
        return response
    except Exception as e:
        print(f"ERROR: Failed to generate response: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ai/test-rag")
async def test_rag_system(request: dict):
    """Test the RAG system with a query."""
    try:
        query = request.get("query", "What is your experience with similar projects?")
        print(f"DEBUG: Testing RAG system with query: {query}")
        
        from services.rag_answer_service import rag_answer_service
        results = await rag_answer_service.search_knowledge_base(
            query=query,
            top_k=5
        )
        
        return {
            "success": True,
            "results": results,
            "qdrant_configured": rag_answer_service.qdrant_client is not None,
            "openai_configured": rag_answer_service.openai_client is not None,
            "collection_name": rag_answer_service.collection_name
        }
    except Exception as e:
        print(f"ERROR: RAG test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "qdrant_configured": False,
            "openai_configured": False
        }

@app.get("/questions/{question_id}/answers", response_model=List[Answer])
async def get_question_answers(question_id: UUID):
    """Get all answers for a question."""
    answers = await response_generation_service.get_question_answers(str(question_id))
    return answers

@app.get("/answers/{answer_id}/sources", response_model=List[Source])
async def get_answer_sources(answer_id: UUID):
    """Get all sources for an answer."""
    sources = await response_generation_service.get_answer_sources(str(answer_id))
    return sources

@app.post("/ai/multi-step-response", response_model=MultiStepResponse)
async def generate_multi_step_response(request: GenerateResponseRequest):
    """Generate AI response using multi-step analysis process."""
    try:
        # Verify question exists
        question = await project_service.get_question(request.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Generate multi-step response
        response = await ai_service.multi_step_generate_response(request)
        
        # Save the final answer
        if response.final_response:
            answer_data = AnswerCreate(
                question_id=request.question_id,
                text=response.final_response,
                confidence=response.overall_confidence
            )
            
            # Create sources from response
            sources = []
            for source_data in response.sources:
                source = SourceCreate(
                    answer_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set after answer creation
                    file_name=source_data.get("fileName", ""),
                    page_number=source_data.get("pageNumber"),
                    relevance=source_data.get("relevance"),
                    text_content=source_data.get("textContent")
                )
                sources.append(source)
            
            await project_service.save_answer(answer_data, sources)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === QUESTION AND ANSWER ENDPOINTS ===

@app.get("/projects/{project_id}/questions", response_model=List[Question])
async def get_project_questions(project_id: UUID):
    """Get all questions for a project."""
    questions = await project_service.get_questions(project_id)
    return questions

@app.get("/projects/{project_id}/questions/by-section")
async def get_questions_by_section(project_id: UUID):
    """Get questions grouped by section."""
    sections = await project_service.get_questions_by_section(project_id)
    return {"sections": sections}

@app.get("/questions/{question_id}", response_model=Question)
async def get_question(question_id: UUID):
    """Get question by ID."""
    question = await project_service.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@app.get("/questions/{question_id}/answer")
async def get_question_answer(question_id: UUID):
    """Get answer for a question with sources."""
    answer_data = await project_service.get_answer_with_sources(question_id)
    if not answer_data:
        raise HTTPException(status_code=404, detail="Answer not found")
    return answer_data

@app.get("/projects/{project_id}/answers")
async def get_project_answers(project_id: UUID):
    """Get all answers for a project."""
    answers = await project_service.get_all_answers(project_id)
    return {"answers": answers}

@app.delete("/answers/{answer_id}")
async def delete_answer(answer_id: UUID):
    """Delete an answer."""
    success = await project_service.delete_answer(answer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Answer not found")
    return {"message": "Answer deleted successfully"}

# === LLAMACLOUD INTEGRATION ENDPOINTS ===

@app.post("/organizations/{org_id}/llamacloud/connect")
async def connect_llamacloud(org_id: UUID, request: LlamaCloudConnectRequest):
    """Connect organization to LlamaCloud project."""
    try:
        # Verify organization exists
        org = await organization_service.get_organization(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Connect to LlamaCloud
        updated_org = await organization_service.connect_llamacloud(
            org_id,
            request.project_id,
            request.project_name,
            request.llama_cloud_org_name
        )
        
        return {
            "success": True,
            "message": "Successfully connected to LlamaCloud",
            "organization": updated_org
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/organizations/{org_id}/llamacloud/disconnect")
async def disconnect_llamacloud(org_id: UUID):
    """Disconnect organization from LlamaCloud."""
    try:
        updated_org = await organization_service.disconnect_llamacloud(org_id)
        if not updated_org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return {
            "success": True,
            "message": "Successfully disconnected from LlamaCloud",
            "organization": updated_org
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/projects/{project_id}/indexes")
async def add_project_index(
    project_id: UUID,
    index_id: str = Form(...),
    index_name: str = Form(...)
):
    """Add an index to a project."""
    try:
        project_index = await project_service.add_project_index(project_id, index_id, index_name)
        return {
            "success": True,
            "project_index": project_index
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# === QDRANT VECTOR DATABASE ENDPOINTS ===

@app.post("/qdrant/quote-collection/initialize")
async def initialize_qdrant_quote_collection():
    """Initialize the quote collection in Qdrant."""
    try:
        qdrant_service = get_qdrant_service()
        success = await qdrant_service.create_quote_collection()
        
        if success:
            return {
                "success": True,
                "message": "Quote collection initialized successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize quote collection")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qdrant/organizations/{org_id}/collections/initialize")
async def initialize_organization_collection(org_id: UUID):
    """Initialize a collection for an organization."""
    try:
        qdrant_service = get_qdrant_service()
        success = await qdrant_service.create_organization_collection(org_id)
        
        if success:
            return {
                "success": True,
                "message": f"Organization collection initialized for {org_id}",
                "collection_name": f"org_{str(org_id).replace('-', '_')}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to initialize organization collection")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qdrant/quotes/index")
async def index_rfp_quote(
    organization_id: UUID = Form(...),
    project_id: UUID = Form(...),
    quote_data: str = Form(...)  # JSON string
):
    """Index RFP quote data in the vector database."""
    try:
        import json
        
        # Parse quote data
        parsed_quote_data = json.loads(quote_data)
        
        qdrant_service = get_qdrant_service()
        success = await qdrant_service.index_rfp_quote(
            quote_data=parsed_quote_data,
            organization_id=organization_id,
            project_id=project_id
        )
        
        if success:
            return {
                "success": True,
                "message": "Quote indexed successfully",
                "project_id": str(project_id),
                "organization_id": str(organization_id)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to index quote")
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in quote_data")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qdrant/search/quotes")
async def search_similar_quotes(
    query: str = Form(...),
    organization_id: UUID = Form(...),
    project_id: Optional[UUID] = Form(None),
    quote_type: Optional[str] = Form(None),
    limit: int = Form(10),
    score_threshold: float = Form(0.7)
):
    """Search for similar quotes in the vector database."""
    try:
        qdrant_service = get_qdrant_service()
        results = await qdrant_service.search_similar_quotes(
            query=query,
            organization_id=organization_id,
            project_id=project_id,
            quote_type=quote_type,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qdrant/search/documents")
async def search_similar_documents(
    query: str = Form(...),
    organization_id: UUID = Form(...),
    project_id: Optional[UUID] = Form(None),
    limit: int = Form(10),
    score_threshold: float = Form(0.7)
):
    """Search for similar document content."""
    try:
        qdrant_service = get_qdrant_service()
        results = await qdrant_service.search_similar_content(
            query=query,
            organization_id=organization_id,
            project_id=project_id,
            limit=limit,
            score_threshold=score_threshold
        )
        
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qdrant/organizations/{org_id}/stats")
async def get_organization_collection_stats(org_id: UUID):
    """Get statistics for an organization's collection."""
    try:
        qdrant_service = get_qdrant_service()
        stats = await qdrant_service.get_collection_stats(org_id)
        
        return {
            "success": True,
            "organization_id": str(org_id),
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qdrant/quote-collection/stats")
async def get_quote_collection_stats():
    """Get statistics for the quote collection."""
    try:
        qdrant_service = get_qdrant_service()
        stats = await qdrant_service.get_quote_collection_stats()
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qdrant/connection/test")
async def test_qdrant_connection_endpoint():
    """Test the Qdrant database connection."""
    result = await qdrant_service.test_connection()
    return result

@app.get("/projects/{project_id}/indexes", response_model=List[ProjectIndex])
async def get_project_indexes(project_id: UUID):
    """Get all indexes for a project."""
    indexes = await project_service.get_project_indexes(project_id)
    return indexes

@app.delete("/projects/{project_id}/indexes/{index_id}")
async def remove_project_index(project_id: UUID, index_id: str):
    """Remove an index from a project."""
    success = await project_service.remove_project_index(project_id, index_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project index not found")
    return {"message": "Index removed from project successfully"}

# === REFERENCE DOCUMENT ENDPOINTS (Simplified for now) ===

# Include simplified endpoints
try:
    from simple_reference_endpoints import router as reference_router
    app.include_router(reference_router)
    print("✅ Simplified reference document endpoints loaded")
except Exception as e:
    print(f"⚠️ Could not load simplified reference endpoints: {e}")

@app.post("/organizations/{organization_id}/reference-documents/upload")
async def upload_reference_document_real(
    organization_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    industry_tags: str = Form(default=""),
    capability_tags: str = Form(default=""),
    project_size: str = Form(default=""),
    geographic_scope: str = Form(default=""),
    confidence_level: str = Form(default="medium"),
    custom_tags: str = Form(default=""),
    description: str = Form(default=""),
    keywords: str = Form(default="")
):
    """Upload a reference document to Qdrant vector database."""
    try:
        print(f"[UPLOAD] Real upload starting for organization {organization_id}")
        print(f"   [INFO] File: {file.filename} ({file.content_type})")
        
        # Read file content
        file_content = await file.read()
        print(f"   [INFO] File size: {len(file_content)} bytes")
        
        # Parse form data
        industry_list = [tag.strip() for tag in industry_tags.split(",") if tag.strip()] if industry_tags else []
        capability_list = [tag.strip() for tag in capability_tags.split(",") if tag.strip()] if capability_tags else []
        custom_list = [tag.strip() for tag in custom_tags.split(",") if tag.strip()] if custom_tags else []
        keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()] if keywords else []
        
        # Create metadata
        metadata = {
            "document_type": document_type,
            "industry_tags": industry_list,
            "capability_tags": capability_list,
            "project_size": project_size,
            "geographic_scope": geographic_scope,
            "organization_id": organization_id,
            "confidence_level": confidence_level,
            "custom_tags": custom_list,
            "description": description,
            "keywords": keyword_list
        }
        
        print(f"   [INFO] Metadata: {metadata}")
        
        # Upload to Qdrant
        from simple_qdrant_upload import simple_qdrant_upload
        qdrant_result = await simple_qdrant_upload.upload_to_qdrant(
            file_content=file_content,
            filename=file.filename,
            metadata=metadata
        )
        
        if qdrant_result["success"]:
            return {
                "success": True,
                "document_id": qdrant_result["document_id"],
                "message": f"Document '{file.filename}' uploaded successfully to Qdrant!",
                "metadata": {
                    "filename": file.filename,
                    "document_type": document_type,
                    "industry_tags": industry_list,
                    "capability_tags": capability_list,
                    "organization_id": organization_id,
                    "upload_date": datetime.now().isoformat(),
                    "vector_id": qdrant_result.get("vector_id"),
                    "text_length": qdrant_result.get("text_length"),
                    "embedding_dimensions": qdrant_result.get("embedding_dimensions")
                }
            }
        else:
            return {
                "success": False,
                "document_id": "",
                "message": f"Upload failed: {qdrant_result.get('error', 'Unknown error')}"
            }
        
    except Exception as e:
        print(f"❌ ERROR: Reference document upload failed: {e}")
        return {
            "success": False,
            "document_id": "",
            "message": f"Upload failed: {str(e)}"
        }

@app.get("/organizations/{organization_id}/reference-documents")
async def get_organization_reference_documents(
    organization_id: UUID,
    document_type: Optional[str] = None,
    is_active: bool = True
):
    """Get all reference documents for an organization."""
    try:
        # Create filter
        filter_params = None
        if document_type:
            from models_reference import DocumentType
            filter_params = ReferenceDocumentFilter(
                document_types=[DocumentType(document_type)],
                is_active=is_active
            )
        else:
            filter_params = ReferenceDocumentFilter(is_active=is_active)
        
        documents = await reference_document_service.get_organization_documents(
            str(organization_id), 
            filter_params
        )
        return {"success": True, "documents": documents}
        
    except Exception as e:
        print(f"ERROR: Failed to fetch reference documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/organizations/{organization_id}/reference-documents/{document_id}")
async def delete_reference_document(organization_id: UUID, document_id: str):
    """Delete a reference document."""
    try:
        success = await reference_document_service.delete_document(
            document_id, 
            str(organization_id)
        )
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except Exception as e:
        print(f"ERROR: Failed to delete reference document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reference-documents/types")
async def get_document_types():
    """Get available document types and tags for the frontend."""
    try:
        # Use hardcoded values for now to avoid import issues
        return {
            "document_types": [
                {"value": "company_profile", "label": "Company Profile"},
                {"value": "case_study", "label": "Case Study"},
                {"value": "technical_specs", "label": "Technical Specs"},
                {"value": "certifications", "label": "Certifications"},
                {"value": "team_bios", "label": "Team Bios"},
                {"value": "pricing_templates", "label": "Pricing Templates"},
                {"value": "methodology", "label": "Methodology"},
                {"value": "partnerships", "label": "Partnerships"},
                {"value": "awards", "label": "Awards"},
                {"value": "other", "label": "Other"}
            ],
            "industry_tags": [
                {"value": "healthcare", "label": "Healthcare"},
                {"value": "finance", "label": "Finance"},
                {"value": "technology", "label": "Technology"},
                {"value": "manufacturing", "label": "Manufacturing"},
                {"value": "government", "label": "Government"},
                {"value": "education", "label": "Education"},
                {"value": "retail", "label": "Retail"},
                {"value": "energy", "label": "Energy"},
                {"value": "telecommunications", "label": "Telecommunications"},
                {"value": "automotive", "label": "Automotive"},
                {"value": "aerospace", "label": "Aerospace"},
                {"value": "other", "label": "Other"}
            ],
            "capability_tags": [
                {"value": "cloud_migration", "label": "Cloud Migration"},
                {"value": "data_analytics", "label": "Data Analytics"},
                {"value": "cybersecurity", "label": "Cybersecurity"},
                {"value": "ai_ml", "label": "AI/ML"},
                {"value": "integration", "label": "Integration"},
                {"value": "mobile_development", "label": "Mobile Development"},
                {"value": "web_development", "label": "Web Development"},
                {"value": "database_management", "label": "Database Management"},
                {"value": "devops", "label": "DevOps"},
                {"value": "consulting", "label": "Consulting"},
                {"value": "project_management", "label": "Project Management"},
                {"value": "quality_assurance", "label": "Quality Assurance"},
                {"value": "ui_ux_design", "label": "UI/UX Design"},
                {"value": "blockchain", "label": "Blockchain"},
                {"value": "iot", "label": "IoT"},
                {"value": "other", "label": "Other"}
            ],
            "project_sizes": [
                {"value": "small", "label": "Small"},
                {"value": "medium", "label": "Medium"},
                {"value": "large", "label": "Large"},
                {"value": "enterprise", "label": "Enterprise"}
            ],
            "geographic_scopes": [
                {"value": "local", "label": "Local"},
                {"value": "regional", "label": "Regional"},
                {"value": "national", "label": "National"},
                {"value": "international", "label": "International"}
            ],
            "confidence_levels": [
                {"value": "high", "label": "High"},
                {"value": "medium", "label": "Medium"},
                {"value": "low", "label": "Low"}
            ]
        }
    except Exception as e:
        print(f"ERROR in get_document_types: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading document types: {str(e)}")

@app.post("/reference-documents/test-search")
async def test_reference_document_search(request: dict):
    """Test search functionality for reference documents."""
    try:
        query = request.get("query", "")
        organization_id = request.get("organization_id", "")
        
        # Test the search using the RAG service
        from services.rag_answer_service import rag_answer_service
        results = await rag_answer_service.search_knowledge_base(
            query=query,
            top_k=10,
            project_filter=organization_id if organization_id else None
        )
        
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_chunks": results.get("results_count", 0)
        }
        
    except Exception as e:
        print(f"ERROR: Reference document search test failed: {e}")
        return {"success": False, "error": str(e)}

@app.post("/ai/generate-response-with-references")
async def generate_response_with_references(request: dict):
    """Generate AI response using reference documents with intelligent filtering."""
    try:
        question = request.get("question", "")
        organization_id = request.get("organization_id", "")
        explicit_filters = request.get("filters", {})
        
        print(f"DEBUG: Generating response with reference documents for org: {organization_id}")
        
        from services.rag_answer_service import rag_answer_service
        response = await rag_answer_service.generate_answer_with_filters(
            question=question,
            organization_id=organization_id,
            explicit_filters=explicit_filters
        )
        
        return response
        
    except Exception as e:
        print(f"ERROR: Failed to generate response with references: {e}")
        return {
            "success": False,
            "error": str(e),
            "filters_applied": {},
            "organization_id": request.get("organization_id", "")
        }

@app.post("/ai/test-smart-filtering")
async def test_smart_filtering(request: dict):
    """Test the smart filtering analysis for RFP questions."""
    try:
        question = request.get("question", "")
        
        from services.rag_answer_service import rag_answer_service
        filters = await rag_answer_service._analyze_question_for_smart_filtering(question)
        
        return {
            "success": True,
            "question": question,
            "suggested_filters": filters,
            "explanation": "Filters were determined by analyzing keywords and question context"
        }
        
    except Exception as e:
        print(f"ERROR: Smart filtering test failed: {e}")
        return {"success": False, "error": str(e)}

# === ERROR HANDLERS ===

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "ValueError"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": "InternalError"}
    )

@app.get("/debug/reference-types")
async def debug_reference_types():
    """Debug endpoint for reference document types."""
    return {
        "message": "Reference document types endpoint working!",
        "document_types": [
            {"value": "company_profile", "label": "Company Profile"},
            {"value": "case_study", "label": "Case Study"},
            {"value": "technical_specs", "label": "Technical Specs"},
            {"value": "certifications", "label": "Certifications"},
            {"value": "team_bios", "label": "Team Bios"}
        ],
        "status": "debug_mode",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/debug/qdrant-connection")
async def debug_qdrant_connection():
    """Debug endpoint to test Qdrant connection."""
    try:
        from simple_qdrant_upload import simple_qdrant_upload
        
        env_status = {
            "QDRANT_URL": "Set" if os.getenv("QDRANT_URL") else "Not set",
            "QDRANT_API_KEY": "Set" if os.getenv("QDRANT_API_KEY") else "Not set",
            "AZURE_OPENAI_ENDPOINT": "Set" if os.getenv("AZURE_OPENAI_ENDPOINT") else "Not set",
            "AZURE_OPENAI_API_KEY": "Set" if os.getenv("AZURE_OPENAI_API_KEY") else "Not set"
        }
        
        # Test Qdrant connection
        qdrant_status = "Not configured"
        if simple_qdrant_upload.qdrant_client:
            try:
                collections = simple_qdrant_upload.qdrant_client.get_collections()
                qdrant_status = f"Connected - {len(collections.collections)} collections found"
            except Exception as e:
                qdrant_status = f"Connection error: {str(e)}"
        
        # Test Azure OpenAI
        openai_status = "Not configured"
        if simple_qdrant_upload.openai_client:
            openai_status = "Configured"
        
        return {
            "message": "Qdrant connection debug info",
            "environment_variables": env_status,
            "qdrant_status": qdrant_status,
            "openai_status": openai_status,
            "collection_name": simple_qdrant_upload.collection_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "message": "Error checking Qdrant connection",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/organizations/{organization_id}/reference-documents/debug")
async def debug_reference_documents(organization_id: str):
    """Debug endpoint for reference documents."""
    return {
        "message": f"Reference documents endpoint for organization {organization_id}",
        "organization_id": organization_id,
        "documents": [],
        "status": "debug_mode"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
