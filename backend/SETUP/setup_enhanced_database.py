"""
Enhanced database setup script for Auto_RFP with full architecture implementation.
This script sets up all tables, indexes, views, and sample data.
"""

import asyncio
import os
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid

# Configure Python path for imports
import config_path

from database_config import connect_db, disconnect_db, database, get_table_name
from models import (
    OrganizationCreate, UserCreate, ProjectCreate, DocumentCreate,
    QuestionCreate, AnswerCreate, SourceCreate, UserRole
)
from services.organization_service import organization_service
from services.project_service import project_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedDatabaseSetup:
    """Enhanced database setup with comprehensive schema and sample data."""
    
    def __init__(self):
        self.db_path = Path("data/auto_rfp_local.db")
        self.sql_dir = Path("sql")
        
    async def setup_complete_database(self):
        """Set up the complete database with all tables and sample data."""
        logger.info("Starting enhanced database setup...")
        
        try:
            # Ensure data directory exists
            self.db_path.parent.mkdir(exist_ok=True)
            
            # Connect to database
            await connect_db()
            logger.info(f"Connected to database: {database.is_connected}")
            
            # Create all tables
            await self.create_all_tables()
            
            # Create sample data
            await self.create_sample_data()
            
            # Verify setup
            await self.verify_setup()
            
            logger.info("Enhanced database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
        finally:
            await disconnect_db()
    
    async def create_all_tables(self):
        """Create all database tables from SQL files."""
        logger.info("Creating database tables...")
        
        # SQL files to execute in order
        sql_files = [
            "04_create_tables_sqlite.sql",  # Basic tables
            "05_create_enhanced_tables.sql"  # Enhanced features
        ]
        
        for sql_file in sql_files:
            sql_path = self.sql_dir / sql_file
            if sql_path.exists():
                logger.info(f"Executing SQL file: {sql_file}")
                await self.execute_sql_file(sql_path)
            else:
                logger.warning(f"SQL file not found: {sql_path}")
    
    async def execute_sql_file(self, sql_path: Path):
        """Execute SQL statements from a file."""
        try:
            with open(sql_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            # Split SQL content into individual statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    try:
                        await database.execute(statement)
                    except Exception as e:
                        logger.warning(f"SQL statement failed: {e}")
                        logger.debug(f"Statement: {statement[:100]}...")
            
            logger.info(f"Successfully executed {sql_path}")
            
        except Exception as e:
            logger.error(f"Error executing {sql_path}: {str(e)}")
            raise
    
    async def create_sample_data(self):
        """Create comprehensive sample data for testing."""
        logger.info("Creating sample data...")
        
        try:
            # Create sample users
            users = await self.create_sample_users()
            
            # Create sample organizations
            organizations = await self.create_sample_organizations(users)
            
            # Create sample projects
            projects = await self.create_sample_projects(organizations)
            
            # Create sample documents and questions
            await self.create_sample_documents_and_questions(projects)
            
            # Create sample AI model configurations
            await self.create_sample_ai_configs(organizations)
            
            # Create sample project templates
            await self.create_sample_templates(users)
            
            logger.info("Sample data created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            raise
    
    async def create_sample_users(self):
        """Create sample users."""
        logger.info("Creating sample users...")
        
        sample_users = [
            {
                "email": "admin@autorfp.com",
                "name": "Admin User"
            },
            {
                "email": "project.manager@company.com",
                "name": "Project Manager"
            },
            {
                "email": "analyst@consulting.com",
                "name": "Business Analyst"
            },
            {
                "email": "demo@user.com",
                "name": "Demo User"
            }
        ]
        
        users = []
        for user_data in sample_users:
            try:
                user = await organization_service.create_user(
                    UserCreate(**user_data)
                )
                users.append(user)
                logger.info(f"Created user: {user.email}")
            except Exception as e:
                logger.warning(f"User creation failed for {user_data['email']}: {e}")
        
        return users
    
    async def create_sample_organizations(self, users):
        """Create sample organizations."""
        logger.info("Creating sample organizations...")
        
        sample_orgs = [
            {
                "name": "Auto RFP Demo Organization",
                "slug": "auto-rfp-demo",
                "description": "Demonstration organization for Auto RFP platform"
            },
            {
                "name": "Government Contracting Corp",
                "slug": "gov-contracting",
                "description": "Government contracting and consulting services"
            },
            {
                "name": "Enterprise Solutions Inc",
                "slug": "enterprise-solutions",
                "description": "Enterprise software and IT solutions provider"
            }
        ]
        
        organizations = []
        for i, org_data in enumerate(sample_orgs):
            try:
                org = await organization_service.create_organization(
                    OrganizationCreate(**org_data),
                    users[min(i, len(users) - 1)].id
                )
                organizations.append(org)
                logger.info(f"Created organization: {org.name}")
                
                # Add additional members
                if len(users) > 1:
                    for j, user in enumerate(users[1:], 1):
                        if j != i:  # Don't add owner again
                            role = UserRole.ADMIN if j == 1 else UserRole.MEMBER
                            await organization_service.add_user_to_organization(
                                user.id, org.id, role
                            )
                            logger.info(f"Added {user.email} to {org.name} as {role}")
                
            except Exception as e:
                logger.warning(f"Organization creation failed for {org_data['name']}: {e}")
        
        return organizations
    
    async def create_sample_projects(self, organizations):
        """Create sample projects."""
        logger.info("Creating sample projects...")
        
        sample_projects = [
            {
                "name": "Federal IT Infrastructure RFP",
                "description": "Large-scale federal government IT infrastructure modernization project"
            },
            {
                "name": "Cloud Migration Services",
                "description": "Enterprise cloud migration and optimization services RFP"
            },
            {
                "name": "Cybersecurity Assessment",
                "description": "Comprehensive cybersecurity assessment and implementation RFP"
            },
            {
                "name": "AI/ML Consulting Services",
                "description": "Artificial intelligence and machine learning consulting RFP"
            },
            {
                "name": "Digital Transformation",
                "description": "Complete digital transformation initiative for large organization"
            }
        ]
        
        projects = []
        for i, project_data in enumerate(sample_projects):
            try:
                org = organizations[i % len(organizations)]
                project = await project_service.create_project(
                    ProjectCreate(
                        organization_id=org.id,
                        **project_data
                    )
                )
                projects.append(project)
                logger.info(f"Created project: {project.name}")
                
            except Exception as e:
                logger.warning(f"Project creation failed for {project_data['name']}: {e}")
        
        return projects
    
    async def create_sample_documents_and_questions(self, projects):
        """Create sample documents and questions."""
        logger.info("Creating sample documents and questions...")
        
        for project in projects[:2]:  # Create for first 2 projects
            try:
                # Create sample document
                document_data = {
                    "name": f"Sample RFP Document - {project.name}",
                    "original_name": f"rfp_{project.name.lower().replace(' ', '_')}.pdf",
                    "file_path": f"/uploads/{project.id}/sample_document.pdf",
                    "file_size": 2048000,  # 2MB
                    "file_type": "application/pdf",
                    "project_id": project.id,
                    "status": "processed"
                }
                
                # Insert document directly into database
                doc_id = str(uuid.uuid4())
                insert_query = f"""
                INSERT INTO documents (id, name, original_name, file_path, file_size, file_type, project_id, status, processed_at)
                VALUES (:id, :name, :original_name, :file_path, :file_size, :file_type, :project_id, :status, :processed_at)
                """
                
                await database.execute(insert_query, {
                    "id": doc_id,
                    "name": document_data["name"],
                    "original_name": document_data["original_name"],
                    "file_path": document_data["file_path"],
                    "file_size": document_data["file_size"],
                    "file_type": document_data["file_type"],
                    "project_id": str(project.id),
                    "status": document_data["status"],
                    "processed_at": datetime.now().isoformat()
                })
                
                logger.info(f"Created document: {document_data['name']}")
                
                # Create sample questions
                sample_questions = [
                    {
                        "text": "What is your company's experience with large-scale enterprise implementations?",
                        "topic": "Company Experience",
                        "section_title": "Vendor Qualifications"
                    },
                    {
                        "text": "Describe your proposed technical architecture and implementation approach.",
                        "topic": "Technical Approach",
                        "section_title": "Technical Requirements"
                    },
                    {
                        "text": "What is your proposed timeline and project milestones?",
                        "topic": "Project Timeline",
                        "section_title": "Project Management"
                    },
                    {
                        "text": "Provide detailed pricing breakdown including all phases and optional components.",
                        "topic": "Pricing",
                        "section_title": "Commercial Terms"
                    },
                    {
                        "text": "How will you ensure data security and compliance with federal regulations?",
                        "topic": "Security & Compliance",
                        "section_title": "Security Requirements"
                    }
                ]
                
                for question_data in sample_questions:
                    question_id = str(uuid.uuid4())
                    question_query = f"""
                    INSERT INTO questions (id, reference_id, text, topic, section_title, project_id, document_id)
                    VALUES (:id, :reference_id, :text, :topic, :section_title, :project_id, :document_id)
                    """
                    
                    await database.execute(question_query, {
                        "id": question_id,
                        "reference_id": f"Q{len(sample_questions)}",
                        "text": question_data["text"],
                        "topic": question_data["topic"],
                        "section_title": question_data["section_title"],
                        "project_id": str(project.id),
                        "document_id": doc_id
                    })
                    
                    # Create sample answer for some questions
                    if hash(question_data["text"]) % 3 == 0:  # Create answers for ~1/3 of questions
                        answer_id = str(uuid.uuid4())
                        sample_answer = f"This is a sample AI-generated answer for the question about {question_data['topic']}. In a real implementation, this would contain detailed, contextual responses based on the organization's capabilities and the specific RFP requirements."
                        
                        answer_query = f"""
                        INSERT INTO answers (id, question_id, text, confidence)
                        VALUES (:id, :question_id, :text, :confidence)
                        """
                        
                        await database.execute(answer_query, {
                            "id": answer_id,
                            "question_id": question_id,
                            "text": sample_answer,
                            "confidence": 0.85
                        })
                        
                        # Create sample source
                        source_id = str(uuid.uuid4())
                        source_query = f"""
                        INSERT INTO sources (id, answer_id, file_name, page_number, document_id, relevance, text_content)
                        VALUES (:id, :answer_id, :file_name, :page_number, :document_id, :relevance, :text_content)
                        """
                        
                        await database.execute(source_query, {
                            "id": source_id,
                            "answer_id": answer_id,
                            "file_name": document_data["original_name"],
                            "page_number": "2",
                            "document_id": doc_id,
                            "relevance": 88,
                            "text_content": f"Source content excerpt related to {question_data['topic']}..."
                        })
                
                logger.info(f"Created {len(sample_questions)} questions for project: {project.name}")
                
            except Exception as e:
                logger.warning(f"Error creating documents/questions for {project.name}: {e}")
    
    async def create_sample_ai_configs(self, organizations):
        """Create sample AI model configurations."""
        logger.info("Creating sample AI configurations...")
        
        for org in organizations:
            try:
                configs = [
                    {
                        "model_name": "gpt-4",
                        "model_type": "chat",
                        "max_tokens": 4000,
                        "temperature": 0.3,
                        "system_prompt": "You are an expert RFP response assistant. Provide detailed, professional responses based on the provided context.",
                        "is_default": True
                    },
                    {
                        "model_name": "text-embedding-3-small",
                        "model_type": "embedding",
                        "max_tokens": 8191,
                        "temperature": 0,
                        "is_default": True
                    }
                ]
                
                for config in configs:
                    config_id = str(uuid.uuid4())
                    config_query = """
                    INSERT INTO ai_model_configs 
                    (id, organization_id, model_name, model_type, max_tokens, temperature, system_prompt, is_default)
                    VALUES (:id, :organization_id, :model_name, :model_type, :max_tokens, :temperature, :system_prompt, :is_default)
                    """
                    
                    await database.execute(config_query, {
                        "id": config_id,
                        "organization_id": str(org.id),
                        **config,
                        "system_prompt": config.get("system_prompt", "")
                    })
                
                logger.info(f"Created AI configurations for: {org.name}")
                
            except Exception as e:
                logger.warning(f"Error creating AI configs for {org.name}: {e}")
    
    async def create_sample_templates(self, users):
        """Create sample project templates."""
        logger.info("Creating sample project templates...")
        
        templates = [
            {
                "name": "Federal Government RFP Template",
                "description": "Standard template for federal government RFP responses",
                "category": "government",
                "template_data": json.dumps({
                    "sections": [
                        "Vendor Qualifications",
                        "Technical Requirements",
                        "Project Management",
                        "Commercial Terms",
                        "Security Requirements"
                    ],
                    "default_questions": [
                        "Company experience and qualifications",
                        "Technical approach and architecture",
                        "Project timeline and milestones",
                        "Pricing and cost breakdown",
                        "Security and compliance measures"
                    ]
                }),
                "is_public": True
            },
            {
                "name": "Enterprise Software RFP Template",
                "description": "Template for enterprise software solution RFPs",
                "category": "enterprise",
                "template_data": json.dumps({
                    "sections": [
                        "Solution Overview",
                        "Technical Specifications",
                        "Implementation Plan",
                        "Support and Maintenance",
                        "Pricing Structure"
                    ]
                }),
                "is_public": True
            }
        ]
        
        for template in templates:
            try:
                template_id = str(uuid.uuid4())
                template_query = """
                INSERT INTO project_templates 
                (id, name, description, category, template_data, is_public, created_by)
                VALUES (:id, :name, :description, :category, :template_data, :is_public, :created_by)
                """
                
                await database.execute(template_query, {
                    "id": template_id,
                    "created_by": str(users[0].id),
                    **template
                })
                
                logger.info(f"Created template: {template['name']}")
                
            except Exception as e:
                logger.warning(f"Error creating template {template['name']}: {e}")
    
    async def verify_setup(self):
        """Verify the database setup was successful."""
        logger.info("Verifying database setup...")
        
        try:
            # Check table counts
            tables_to_check = [
                "users", "organizations", "organization_users", "projects", 
                "documents", "questions", "answers", "sources"
            ]
            
            for table in tables_to_check:
                count_query = f"SELECT COUNT(*) as count FROM {table}"
                result = await database.fetch_one(count_query)
                count = result["count"] if result else 0
                logger.info(f"Table {table}: {count} records")
            
            # Check views
            view_query = "SELECT COUNT(*) as count FROM project_summary"
            result = await database.fetch_one(view_query)
            logger.info(f"Project summary view: {result['count']} records")
            
            logger.info("Database verification completed successfully!")
            
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise

async def main():
    """Main setup function."""
    setup = EnhancedDatabaseSetup()
    await setup.setup_complete_database()

if __name__ == "__main__":
    asyncio.run(main())