"""
PostgreSQL database setup script for Auto_RFP platform.
This script sets up the PostgreSQL database with all tables, indexes, views, and sample data.
"""

import asyncio
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json
import uuid

# Configure Python path for imports
import config_path

from database_config import connect_db, disconnect_db, database
from models import (
    OrganizationCreate, UserCreate, ProjectCreate, DocumentCreate,
    QuestionCreate, AnswerCreate, SourceCreate, UserRole
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostgreSQLDatabaseSetup:
    """PostgreSQL database setup with comprehensive schema and sample data."""
    
    def __init__(self):
        self.sql_dir = Path("sql")
        
    async def setup_complete_database(self):
        """Set up the complete PostgreSQL database with all tables and sample data."""
        logger.info("Starting PostgreSQL database setup...")
        
        try:
            # Install required packages first
            await self.install_requirements()
            
            # Connect to database
            await connect_db()
            logger.info(f"Connected to database: {database.is_connected}")
            
            # Create all tables
            await self.create_all_tables()
            
            # Create sample data
            await self.create_sample_data()
            
            # Verify setup
            await self.verify_setup()
            
            logger.info("PostgreSQL database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise
        finally:
            await disconnect_db()
    
    async def install_requirements(self):
        """Install required Python packages for PostgreSQL."""
        logger.info("Installing PostgreSQL requirements...")
        
        try:
            import subprocess
            import sys
            
            # Install PostgreSQL drivers
            packages = ["psycopg2-binary", "asyncpg"]
            
            for package in packages:
                try:
                    __import__(package.replace("-", "_"))
                    logger.info(f"{package} is already installed")
                except ImportError:
                    logger.info(f"Installing {package}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    logger.info(f"{package} installed successfully")
                    
        except Exception as e:
            logger.warning(f"Could not install requirements automatically: {e}")
            logger.info("Please install manually: pip install psycopg2-binary asyncpg")
    
    async def create_all_tables(self):
        """Create all database tables from SQL files."""
        logger.info("Creating database tables...")
        
        # Start with minimal schema
        sql_file = "00_minimal_schema.sql"
        sql_path = self.sql_dir / sql_file
        
        if sql_path.exists():
            logger.info(f"Executing minimal schema: {sql_file}")
            await self.execute_sql_file(sql_path)
        else:
            logger.error(f"SQL file not found: {sql_path}")
            raise FileNotFoundError(f"Required SQL file not found: {sql_path}")
    
    async def execute_sql_file(self, sql_path: Path):
        """Execute SQL statements from a file."""
        try:
            with open(sql_path, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            # Remove comments and split on semicolon
            lines = sql_content.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('--'):
                    clean_lines.append(line)
            
            clean_sql = ' '.join(clean_lines)
            statements = [stmt.strip() for stmt in clean_sql.split(';') if stmt.strip()]
            
            logger.info(f"Executing {len(statements)} SQL statements...")
            
            for i, statement in enumerate(statements):
                if statement:
                    try:
                        await database.execute(statement)
                        logger.info(f"✓ Statement {i+1}/{len(statements)} executed successfully")
                    except Exception as e:
                        logger.error(f"✗ Statement {i+1}/{len(statements)} failed: {e}")
                        logger.error(f"Failed statement: {statement[:100]}...")
                        # Don't continue if table creation fails
                        if "CREATE TABLE" in statement.upper():
                            raise e
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
                user_id = str(uuid.uuid4())
                
                query = """
                    INSERT INTO users (id, email, name, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id, email, name, created_at, updated_at
                """
                
                now = datetime.now()
                result = await database.fetch_one(query, user_id, user_data["email"], user_data["name"], now, now)
                
                users.append({
                    "id": result["id"],
                    "email": result["email"],
                    "name": result["name"],
                    "created_at": result["created_at"],
                    "updated_at": result["updated_at"]
                })
                
                logger.info(f"Created user: {user_data['email']}")
                
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
                org_id = str(uuid.uuid4())
                now = datetime.now()
                
                # Create organization
                org_query = """
                    INSERT INTO organizations (id, name, slug, description, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id, name, slug, description, created_at, updated_at
                """
                
                org_result = await database.fetch_one(
                    org_query, 
                    org_id, 
                    org_data["name"], 
                    org_data["slug"], 
                    org_data["description"], 
                    now, 
                    now
                )
                
                organizations.append({
                    "id": org_result["id"],
                    "name": org_result["name"],
                    "slug": org_result["slug"],
                    "description": org_result["description"],
                    "created_at": org_result["created_at"],
                    "updated_at": org_result["updated_at"]
                })
                
                logger.info(f"Created organization: {org_data['name']}")
                
                # Add organization owner
                owner_id = users[min(i, len(users) - 1)]["id"]
                
                org_user_query = """
                    INSERT INTO organization_users (id, user_id, organization_id, role, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """
                
                await database.execute(
                    org_user_query,
                    str(uuid.uuid4()),
                    owner_id,
                    org_id,
                    "owner",
                    now,
                    now
                )
                
                # Add additional members
                if len(users) > 1:
                    for j, user in enumerate(users[1:], 1):
                        if j != i:  # Don't add owner again
                            role = "admin" if j == 1 else "member"
                            await database.execute(
                                org_user_query,
                                str(uuid.uuid4()),
                                user["id"],
                                org_id,
                                role,
                                now,
                                now
                            )
                            logger.info(f"Added {user['email']} to {org_data['name']} as {role}")
                
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
                project_id = str(uuid.uuid4())
                now = datetime.now()
                
                query = """
                    INSERT INTO projects (id, name, description, organization_id, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id, name, description, organization_id, created_at, updated_at
                """
                
                result = await database.fetch_one(
                    query,
                    project_id,
                    project_data["name"],
                    project_data["description"],
                    org["id"],
                    now,
                    now
                )
                
                projects.append({
                    "id": result["id"],
                    "name": result["name"],
                    "description": result["description"],
                    "organization_id": result["organization_id"],
                    "created_at": result["created_at"],
                    "updated_at": result["updated_at"]
                })
                
                logger.info(f"Created project: {project_data['name']}")
                
            except Exception as e:
                logger.warning(f"Project creation failed for {project_data['name']}: {e}")
        
        return projects
    
    async def create_sample_documents_and_questions(self, projects):
        """Create sample documents and questions."""
        logger.info("Creating sample documents and questions...")
        
        for project in projects[:2]:  # Create for first 2 projects
            try:
                # Create sample document
                doc_id = str(uuid.uuid4())
                now = datetime.now()
                
                doc_query = """
                    INSERT INTO documents (id, name, original_name, file_path, file_size, file_type, project_id, uploaded_at, processed_at, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """
                
                doc_result = await database.fetch_one(
                    doc_query,
                    doc_id,
                    f"Sample RFP Document - {project['name']}",
                    f"rfp_{project['name'].lower().replace(' ', '_')}.pdf",
                    f"storage/documents/org_{project['organization_id']}/project_{project['id']}/{doc_id}.pdf",
                    2048000,  # 2MB
                    "application/pdf",
                    project["id"],
                    now,
                    now,
                    "processed"
                )
                
                logger.info(f"Created document for project: {project['name']}")
                
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
                
                for j, question_data in enumerate(sample_questions):
                    question_id = str(uuid.uuid4())
                    
                    question_query = """
                        INSERT INTO questions (id, reference_id, text, topic, section_title, project_id, document_id, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        RETURNING id
                    """
                    
                    question_result = await database.fetch_one(
                        question_query,
                        question_id,
                        f"Q{j+1}",
                        question_data["text"],
                        question_data["topic"],
                        question_data["section_title"],
                        project["id"],
                        doc_id,
                        now,
                        now
                    )
                    
                    # Create sample answer for some questions
                    if j % 3 == 0:  # Create answers for ~1/3 of questions
                        answer_id = str(uuid.uuid4())
                        sample_answer = f"This is a sample AI-generated answer for the question about {question_data['topic']}. In a real implementation, this would contain detailed, contextual responses based on the organization's capabilities and the specific RFP requirements."
                        
                        answer_query = """
                            INSERT INTO answers (id, question_id, text, confidence, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6)
                            RETURNING id
                        """
                        
                        answer_result = await database.fetch_one(
                            answer_query,
                            answer_id,
                            question_id,
                            sample_answer,
                            0.85,
                            now,
                            now
                        )
                        
                        # Create sample source
                        source_id = str(uuid.uuid4())
                        source_query = """
                            INSERT INTO sources (id, answer_id, file_name, page_number, document_id, relevance, text_content, created_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """
                        
                        await database.execute(
                            source_query,
                            source_id,
                            answer_id,
                            f"rfp_{project['name'].lower().replace(' ', '_')}.pdf",
                            "2",
                            doc_id,
                            88,
                            f"Source content excerpt related to {question_data['topic']}...",
                            now
                        )
                
                logger.info(f"Created {len(sample_questions)} questions for project: {project['name']}")
                
            except Exception as e:
                logger.warning(f"Error creating documents/questions for {project['name']}: {e}")
    
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
                    now = datetime.now()
                    
                    config_query = """
                        INSERT INTO ai_model_configs 
                        (id, organization_id, model_name, model_type, max_tokens, temperature, system_prompt, is_default, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """
                    
                    await database.execute(
                        config_query,
                        config_id,
                        org["id"],
                        config["model_name"],
                        config["model_type"],
                        config["max_tokens"],
                        config["temperature"],
                        config.get("system_prompt", ""),
                        config["is_default"],
                        now,
                        now
                    )
                
                logger.info(f"Created AI configurations for: {org['name']}")
                
            except Exception as e:
                logger.warning(f"Error creating AI configs for {org['name']}: {e}")
    
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
                now = datetime.now()
                
                template_query = """
                    INSERT INTO project_templates 
                    (id, name, description, category, template_data, is_public, created_by, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """
                
                await database.execute(
                    template_query,
                    template_id,
                    template["name"],
                    template["description"],
                    template["category"],
                    template["template_data"],
                    template["is_public"],
                    users[0]["id"],
                    now,
                    now
                )
                
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
            
            # Check if all tables were created successfully
            logger.info("All essential tables created successfully!")
            
            logger.info("Database verification completed successfully!")
            
        except Exception as e:
            logger.error(f"Database verification failed: {str(e)}")
            raise

async def main():
    """Main setup function."""
    setup = PostgreSQLDatabaseSetup()
    await setup.setup_complete_database()

if __name__ == "__main__":
    asyncio.run(main())