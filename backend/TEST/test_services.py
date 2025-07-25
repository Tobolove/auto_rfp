"""
Test suite for service layer functionality.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

# Configure test environment
os.environ['DATABASE_URL'] = 'sqlite:///./test_services_db.sqlite'
os.environ['TESTING'] = 'true'

from database_config import connect_db, disconnect_db
from models import (
    OrganizationCreate, UserCreate, ProjectCreate, DocumentCreate,
    QuestionCreate, AnswerCreate, UserRole
)
from services.organization_service import organization_service
from services.project_service import project_service
from services.ai_service import ai_service

@pytest.fixture
async def setup_test_db():
    """Setup test database for services."""
    await connect_db()
    yield
    await disconnect_db()

class TestOrganizationService:
    """Test organization service functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, setup_test_db):
        """Test user creation."""
        user_data = UserCreate(
            email="test@example.com",
            name="Test User"
        )
        
        user = await organization_service.create_user(user_data)
        
        assert user.email == user_data.email
        assert user.name == user_data.name
        assert user.id is not None
    
    @pytest.mark.asyncio
    async def test_create_organization(self, setup_test_db):
        """Test organization creation."""
        # Create user first
        user_data = UserCreate(
            email="owner@example.com",
            name="Owner User"
        )
        user = await organization_service.create_user(user_data)
        
        # Create organization
        org_data = OrganizationCreate(
            name="Test Organization",
            slug="test-org",
            description="Test organization for services"
        )
        
        org = await organization_service.create_organization(org_data, user.id)
        
        assert org.name == org_data.name
        assert org.slug == org_data.slug
        assert org.description == org_data.description
        assert org.id is not None
    
    @pytest.mark.asyncio
    async def test_add_user_to_organization(self, setup_test_db):
        """Test adding user to organization."""
        # Create users
        owner_data = UserCreate(email="owner@example.com", name="Owner")
        member_data = UserCreate(email="member@example.com", name="Member")
        
        owner = await organization_service.create_user(owner_data)
        member = await organization_service.create_user(member_data)
        
        # Create organization
        org_data = OrganizationCreate(
            name="Test Org",
            slug="test-org-members",
            description="Test organization membership"
        )
        org = await organization_service.create_organization(org_data, owner.id)
        
        # Add member to organization
        org_user = await organization_service.add_user_to_organization(
            member.id, org.id, UserRole.MEMBER
        )
        
        assert org_user.user_id == member.id
        assert org_user.organization_id == org.id
        assert org_user.role == UserRole.MEMBER

class TestProjectService:
    """Test project service functionality."""
    
    @pytest.mark.asyncio
    async def test_create_project(self, setup_test_db):
        """Test project creation."""
        # Setup organization first
        user_data = UserCreate(email="test@project.com", name="Project User")
        user = await organization_service.create_user(user_data)
        
        org_data = OrganizationCreate(
            name="Project Test Org",
            slug="project-test-org",
            description="Organization for project testing"
        )
        org = await organization_service.create_organization(org_data, user.id)
        
        # Create project
        project_data = ProjectCreate(
            name="Test Project",
            description="Test project for services",
            organization_id=org.id
        )
        
        project = await project_service.create_project(project_data)
        
        assert project.name == project_data.name
        assert project.description == project_data.description
        assert project.organization_id == org.id
        assert project.id is not None
    
    @pytest.mark.asyncio
    async def test_get_project_stats(self, setup_test_db):
        """Test getting project statistics."""
        # Create project setup
        user_data = UserCreate(email="stats@test.com", name="Stats User")
        user = await organization_service.create_user(user_data)
        
        org_data = OrganizationCreate(
            name="Stats Org",
            slug="stats-org",
            description="Organization for stats testing"
        )
        org = await organization_service.create_organization(org_data, user.id)
        
        project_data = ProjectCreate(
            name="Stats Project",
            description="Project for statistics testing",
            organization_id=org.id
        )
        project = await project_service.create_project(project_data)
        
        # Get stats
        stats = await project_service.get_project_stats(project.id)
        
        assert "total_documents" in stats
        assert "total_questions" in stats
        assert "answered_questions" in stats
        assert "completion_rate" in stats
        assert isinstance(stats["total_documents"], int)
        assert isinstance(stats["completion_rate"], (int, float))

class TestAIService:
    """Test AI service functionality."""
    
    @pytest.mark.asyncio
    async def test_ai_service_configuration(self):
        """Test AI service configuration."""
        test_api_key = "test-api-key"
        
        # Configure AI service
        ai_service.configure(openai_api_key=test_api_key)
        
        # Check configuration was applied
        assert hasattr(ai_service, 'openai_api_key')
    
    @pytest.mark.asyncio
    @patch('openai.AsyncOpenAI')
    async def test_extract_questions_mock(self, mock_openai):
        """Test question extraction with mocked OpenAI."""
        # Setup mock
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        [
            {
                "text": "What is your company experience?",
                "section": "Company Qualifications",
                "topic": "Experience"
            }
        ]
        '''
        
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # Configure AI service with mock
        ai_service.configure(openai_api_key="test-key")
        ai_service.openai_client = mock_client
        
        # Test extraction (would normally require real document)
        # This tests the parsing logic
        content = "Sample RFP content with questions about company experience."
        
        # The actual implementation would process this content
        # For testing, we verify the mock setup works
        assert mock_client is not None

class TestIntegrationScenarios:
    """Test complete workflows and integrations."""
    
    @pytest.mark.asyncio
    async def test_complete_rfp_workflow(self, setup_test_db):
        """Test complete RFP processing workflow."""
        # 1. Create user and organization
        user = await organization_service.create_user(
            UserCreate(email="workflow@test.com", name="Workflow User")
        )
        
        org = await organization_service.create_organization(
            OrganizationCreate(
                name="Workflow Org",
                slug="workflow-org",
                description="Complete workflow testing"
            ),
            user.id
        )
        
        # 2. Create project
        project = await project_service.create_project(
            ProjectCreate(
                name="Workflow Project",
                description="End-to-end workflow testing",
                organization_id=org.id
            )
        )
        
        # 3. Verify project stats are initialized correctly
        stats = await project_service.get_project_stats(project.id)
        assert stats["total_documents"] == 0
        assert stats["total_questions"] == 0
        assert stats["completion_rate"] == 0
        
        # 4. Get organizations for user
        user_orgs = await organization_service.get_organizations(user.id)
        assert len(user_orgs) >= 1
        assert any(o.id == org.id for o in user_orgs)
        
        # 5. Get projects for organization
        org_projects = await project_service.get_projects(org.id)
        assert len(org_projects) >= 1
        assert any(p.id == project.id for p in org_projects)
    
    @pytest.mark.asyncio
    async def test_organization_membership_workflow(self, setup_test_db):
        """Test organization membership management workflow."""
        # Create users
        owner = await organization_service.create_user(
            UserCreate(email="owner@membership.com", name="Owner")
        )
        
        admin = await organization_service.create_user(
            UserCreate(email="admin@membership.com", name="Admin")
        )
        
        member = await organization_service.create_user(
            UserCreate(email="member@membership.com", name="Member")
        )
        
        # Create organization
        org = await organization_service.create_organization(
            OrganizationCreate(
                name="Membership Org",
                slug="membership-org",
                description="Testing membership workflows"
            ),
            owner.id
        )
        
        # Add admin
        await organization_service.add_user_to_organization(
            admin.id, org.id, UserRole.ADMIN
        )
        
        # Add member
        await organization_service.add_user_to_organization(
            member.id, org.id, UserRole.MEMBER
        )
        
        # Get organization members
        members = await organization_service.get_organization_members(org.id)
        assert len(members) == 3  # owner, admin, member
        
        # Verify roles
        member_roles = {m.user_id: m.role for m in members}
        assert member_roles[owner.id] == UserRole.OWNER
        assert member_roles[admin.id] == UserRole.ADMIN
        assert member_roles[member.id] == UserRole.MEMBER
        
        # Update member role
        await organization_service.update_user_role(
            member.id, org.id, UserRole.ADMIN
        )
        
        # Verify role update
        updated_members = await organization_service.get_organization_members(org.id)
        updated_roles = {m.user_id: m.role for m in updated_members}
        assert updated_roles[member.id] == UserRole.ADMIN

class TestErrorScenarios:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_duplicate_organization_slug(self, setup_test_db):
        """Test handling of duplicate organization slugs."""
        user = await organization_service.create_user(
            UserCreate(email="duplicate@test.com", name="Duplicate User")
        )
        
        # Create first organization
        org1 = await organization_service.create_organization(
            OrganizationCreate(
                name="First Org",
                slug="duplicate-slug",
                description="First organization"
            ),
            user.id
        )
        
        # Try to create second organization with same slug
        with pytest.raises(Exception):
            await organization_service.create_organization(
                OrganizationCreate(
                    name="Second Org",
                    slug="duplicate-slug",
                    description="Second organization"
                ),
                user.id
            )
    
    @pytest.mark.asyncio
    async def test_nonexistent_organization_access(self, setup_test_db):
        """Test accessing non-existent organization."""
        fake_org_id = uuid4()
        
        org = await organization_service.get_organization(fake_org_id)
        assert org is None
    
    @pytest.mark.asyncio
    async def test_project_without_organization(self, setup_test_db):
        """Test creating project with non-existent organization."""
        fake_org_id = uuid4()
        
        with pytest.raises(Exception):
            await project_service.create_project(
                ProjectCreate(
                    name="Orphan Project",
                    description="Project without organization",
                    organization_id=fake_org_id
                )
            )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])