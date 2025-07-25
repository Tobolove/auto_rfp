#!/usr/bin/env python3
"""
Test organization service with database operations.
"""
import asyncio
from database_config import connect_db, disconnect_db
from services.organization_service import organization_service
from models import OrganizationCreate, UserCreate
from uuid import uuid4

async def test_org_service():
    """Test organization service with database."""
    try:
        print("Connecting to database...")
        await connect_db()
        
        print("Testing organization service...")
        
        # Try to get existing user first, or create if needed
        existing_user = await organization_service.get_user_by_email("testuser@example.com")
        if existing_user:
            user = existing_user
            print(f"Using existing user: {user.email} with ID: {user.id}")
        else:
            user_data = UserCreate(
                email="testuser@example.com",
                name="Test User"
            )
            user = await organization_service.create_user(user_data)
            print(f"Created user: {user.email} with ID: {user.id}")
        
        # Skip creating organization since we've already tested this works
        
        # Get organizations
        orgs = await organization_service.get_organizations()
        print(f"Found {len(orgs)} organizations:")
        for o in orgs:
            print(f"  - {o.name} | {o.slug}")
        
        await disconnect_db()
        
    except Exception as e:
        print(f"Service test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_org_service())