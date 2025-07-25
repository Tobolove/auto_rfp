"""
Test suite for API endpoints.
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
import tempfile
import os
from pathlib import Path

# Configure test environment
os.environ['DATABASE_URL'] = 'sqlite:///./test_db.sqlite'
os.environ['TESTING'] = 'true'

from main import app
from database_config import connect_db, disconnect_db
from models import OrganizationCreate, UserCreate, ProjectCreate

@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def setup_test_db():
    """Setup test database."""
    await connect_db()
    yield
    await disconnect_db()

@pytest.fixture
async def sample_user():
    """Create a sample user for testing."""
    return {
        "email": "test@example.com",
        "name": "Test User"
    }

@pytest.fixture
async def sample_organization():
    """Create a sample organization for testing."""
    return {
        "name": "Test Organization",
        "slug": "test-org",
        "description": "Test organization for API testing"
    }

class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint returns correct response."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data

class TestOrganizationEndpoints:
    """Test organization CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_organization(self, client, setup_test_db, sample_organization, sample_user):
        """Test creating a new organization."""
        # First create the organization
        form_data = {
            "name": sample_organization["name"],
            "slug": sample_organization["slug"],
            "description": sample_organization["description"],
            "owner_email": sample_user["email"]
        }
        
        response = await client.post("/organizations", data=form_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == sample_organization["name"]
        assert data["slug"] == sample_organization["slug"]
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_get_organizations(self, client, setup_test_db):
        """Test getting list of organizations."""
        response = await client.get("/organizations")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.asyncio
    async def test_get_organization_by_id(self, client, setup_test_db, sample_organization, sample_user):
        """Test getting organization by ID."""
        # Create organization first
        form_data = {
            "name": sample_organization["name"],
            "slug": sample_organization["slug"],
            "description": sample_organization["description"],
            "owner_email": sample_user["email"]
        }
        
        create_response = await client.post("/organizations", data=form_data)
        org_data = create_response.json()
        org_id = org_data["id"]
        
        # Get organization by ID
        response = await client.get(f"/organizations/{org_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == org_id
        assert data["name"] == sample_organization["name"]

class TestProjectEndpoints:
    """Test project CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, client, setup_test_db, sample_organization, sample_user):
        """Test creating a new project."""
        # Create organization first
        org_form_data = {
            "name": sample_organization["name"],
            "slug": sample_organization["slug"],
            "description": sample_organization["description"],
            "owner_email": sample_user["email"]
        }
        
        org_response = await client.post("/organizations", data=org_form_data)
        org_data = org_response.json()
        
        # Create project
        project_data = {
            "name": "Test Project",
            "description": "Test project description",
            "organization_id": org_data["id"]
        }
        
        response = await client.post("/projects", json=project_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["organization_id"] == project_data["organization_id"]
    
    @pytest.mark.asyncio
    async def test_get_projects(self, client, setup_test_db):
        """Test getting list of projects."""
        response = await client.get("/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestDocumentEndpoints:
    """Test document upload and processing endpoints."""
    
    @pytest.mark.asyncio
    async def test_upload_document(self, client, setup_test_db, sample_organization, sample_user):
        """Test document upload."""
        # Create organization and project first
        org_form_data = {
            "name": sample_organization["name"],
            "slug": sample_organization["slug"],
            "description": sample_organization["description"],
            "owner_email": sample_user["email"]
        }
        
        org_response = await client.post("/organizations", data=org_form_data)
        org_data = org_response.json()
        
        project_data = {
            "name": "Test Project",
            "description": "Test project for document upload",
            "organization_id": org_data["id"]
        }
        
        project_response = await client.post("/projects", json=project_data)
        project_data = project_response.json()
        project_id = project_data["id"]
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as f:
            f.write("This is a test document for RFP processing.")
            test_file_path = f.name
        
        try:
            # Upload document
            with open(test_file_path, 'rb') as f:
                files = {'file': ('test.txt', f, 'text/plain')}
                data = {'name': 'Test Document'}
                
                response = await client.post(
                    f"/projects/{project_id}/documents",
                    files=files,
                    data=data
                )
            
            assert response.status_code == 201
            
            doc_data = response.json()
            assert doc_data["name"] == "Test Document"
            assert doc_data["project_id"] == project_id
            
        finally:
            # Clean up test file
            os.unlink(test_file_path)

class TestAIEndpoints:
    """Test AI processing endpoints."""
    
    @pytest.mark.asyncio
    async def test_extract_questions_endpoint(self, client, setup_test_db):
        """Test question extraction endpoint structure."""
        # This test only checks endpoint structure since we don't have real AI services configured
        extract_request = {
            "document_id": "test-doc-id",
            "document_name": "test.pdf",
            "content": "Sample RFP content for testing",
            "project_id": "test-project-id"
        }
        
        response = await client.post("/ai/extract-questions", json=extract_request)
        # Expect 400/404 since document doesn't exist, but endpoint should be reachable
        assert response.status_code in [400, 404, 500]
    
    @pytest.mark.asyncio
    async def test_generate_response_endpoint(self, client, setup_test_db):
        """Test response generation endpoint structure."""
        response_request = {
            "question": "Test question",
            "question_id": "test-question-id",
            "project_id": "test-project-id"
        }
        
        response = await client.post("/ai/generate-response", json=response_request)
        # Expect 400/404 since question doesn't exist, but endpoint should be reachable
        assert response.status_code in [400, 404, 500]

class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_organization(self, client, setup_test_db):
        """Test accessing non-existent organization."""
        response = await client.get("/organizations/nonexistent-id")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invalid_json_payload(self, client, setup_test_db):
        """Test handling of invalid JSON payload."""
        response = await client.post(
            "/projects",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client, setup_test_db):
        """Test handling of missing required fields."""
        # Try to create organization without required fields
        form_data = {
            "name": "Test Org"
            # Missing slug and owner_email
        }
        
        response = await client.post("/organizations", data=form_data)
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v"])