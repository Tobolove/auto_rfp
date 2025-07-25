#!/usr/bin/env python3
"""
Test script for document processing pipeline.
"""

import asyncio
import sys
import os
import uuid
from pathlib import Path

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.document_service import document_service
from services.project_service import project_service
from services.organization_service import organization_service
from database_config import database

async def test_document_processing():
    """Test the complete document processing pipeline."""
    print("🔧 Testing Document Processing Pipeline")
    print("=" * 50)
    
    try:
        # Connect to database
        await database.connect()
        print("✅ Database connected successfully")
        
        # Create test user first with unique identifier
        print("\n👤 Creating test user...")
        test_user_id = uuid.uuid4()
        users_table = "users"
        unique_suffix = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for uniqueness
        
        # Insert test user into database
        try:
            user_query = f"""
                INSERT INTO {users_table} (id, email, name, created_at, updated_at)
                VALUES (:id, :email, :name, :created_at, :updated_at)
            """
            from datetime import datetime
            await database.execute(user_query, {
                "id": str(test_user_id),
                "email": f"test-{unique_suffix}@example.com",
                "name": f"Test User {unique_suffix}",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            print(f"✅ Test user created: {test_user_id}")
        except Exception as e:
            print(f"⚠️  User creation failed: {e}")
        
        # Create test organization with unique slug
        print("\n📋 Creating test organization...")
        from models import OrganizationCreate
        
        org_data = OrganizationCreate(
            name=f"Test Organization {unique_suffix}",
            slug=f"test-organization-{unique_suffix}",
            description="Test organization for document processing"
        )
        test_org = await organization_service.create_organization(org_data, test_user_id)
        print(f"✅ Organization created: {test_org.name} (ID: {test_org.id})")
        
        # Create test project
        print("\n📁 Creating test project...")
        from models import ProjectCreate
        
        project_data = ProjectCreate(
            name=f"Test Project {unique_suffix}",
            description="Testing document processing",
            organization_id=test_org.id
        )
        test_project = await project_service.create_project(project_data)
        print(f"✅ Project created: {test_project.name} (ID: {test_project.id})")
        
        # Create test document content
        test_content = """
        TEST RFP DOCUMENT
        
        1. TECHNICAL REQUIREMENTS
        
        Question 1: What is your experience with cloud infrastructure?
        Please provide details about your AWS, Azure, or GCP experience.
        
        Question 2: Describe your security measures.
        How do you ensure data protection and compliance?
        
        2. COMPANY INFORMATION
        
        Question 3: What is your company's track record?
        Please provide references from similar projects.
        
        Question 4: What are your pricing models?
        Describe your cost structure and payment terms.
        """
        
        print("\n📄 Testing document upload and processing...")
        
        # Test document upload
        document = await document_service.upload_document(
            file_content=test_content.encode('utf-8'),
            filename="test_rfp.txt",
            project_id=str(test_project.id),
            content_type="text/plain"
        )
        
        print(f"✅ Document uploaded: {document.name}")
        print(f"   - ID: {document.id}")
        print(f"   - Status: {document.status}")
        print(f"   - File path: {document.file_path}")
        print(f"   - Size: {document.file_size} bytes")
        
        # Wait a moment for processing
        await asyncio.sleep(2)
        
        # Check document status
        updated_doc = await document_service.get_document(str(document.id))
        if updated_doc:
            print(f"📊 Document processing status: {updated_doc.status}")
            if updated_doc.processed_at:
                print(f"   - Processed at: {updated_doc.processed_at}")
        
        # List project documents
        print("\n📚 Listing project documents...")
        project_docs = await document_service.get_project_documents(str(test_project.id))
        print(f"✅ Found {len(project_docs)} documents in project")
        
        for doc in project_docs:
            print(f"   📄 {doc.name} - Status: {doc.status}")
        
        # Test question extraction (if document is processed)
        if updated_doc and updated_doc.status == "processed":
            print("\n🤖 Testing question extraction...")
            try:
                from services.question_extraction_service import question_extraction_service
                from models import ExtractQuestionsRequest
                
                request = ExtractQuestionsRequest(
                    document_id=document.id,
                    project_id=test_project.id
                )
                
                extraction_result = await question_extraction_service.extract_questions_from_document(request)
                
                print(f"✅ Question extraction completed")
                print(f"   - Sections found: {len(extraction_result.sections)}")
                
                total_questions = sum(len(section.questions) for section in extraction_result.sections)
                print(f"   - Total questions: {total_questions}")
                
                # Show extracted sections and questions
                for i, section in enumerate(extraction_result.sections, 1):
                    print(f"   📁 Section {i}: {section.title}")
                    for j, question in enumerate(section.questions, 1):
                        print(f"      ❓ Q{j}: {question.text[:100]}...")
                        
            except Exception as e:
                print(f"❌ Question extraction failed: {e}")
        else:
            print("⚠️  Document not processed yet, skipping question extraction test")
        
        print("\n🧹 Cleaning up test data...")
        
        # Clean up - delete test document
        await document_service.delete_document(str(document.id))
        print("✅ Test document deleted")
        
        # Clean up - delete test project
        await project_service.delete_project(str(test_project.id))
        print("✅ Test project deleted")
        
        # Clean up - delete test organization
        await organization_service.delete_organization(str(test_org.id))
        print("✅ Test organization deleted")
        
        # Clean up - delete test user
        try:
            await database.execute(f"DELETE FROM {users_table} WHERE id = :user_id", {"user_id": str(test_user_id)})
            print("✅ Test user deleted")
        except Exception as e:
            print(f"⚠️  User cleanup failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect from database
        await database.disconnect()
        print("\n🔒 Database disconnected")
    
    print("\n" + "=" * 50)
    print("✅ Document processing test completed")

async def test_storage_service():
    """Test the file storage service independently."""
    print("\n🗄️  Testing File Storage Service")
    print("-" * 30)
    
    try:
        from services.file_storage_service import file_storage_service
        
        # Test file storage
        test_content = b"This is a test document for storage testing."
        
        result = await file_storage_service.store_document(
            file_content=test_content,
            filename="storage_test.txt",
            organization_id="test-org",
            project_id="test-project"
        )
        
        print(f"✅ File storage test successful")
        print(f"   - Document ID: {result['document_id']}")
        print(f"   - File path: {result['file_path']}")
        print(f"   - Is duplicate: {result['is_duplicate']}")
        
        # Test file retrieval
        retrieved_content = await file_storage_service.get_document(result['relative_path'])
        if retrieved_content == test_content:
            print("✅ File retrieval test successful")
        else:
            print("❌ File retrieval test failed - content mismatch")
        
        # Clean up
        await file_storage_service.delete_document(result['relative_path'])
        print("✅ Storage cleanup completed")
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("🚀 Starting Document Processing Tests")
    print("=" * 60)
    
    # Test storage service first
    await test_storage_service()
    
    # Test full document processing pipeline
    await test_document_processing()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())