#!/usr/bin/env python3
"""
Test organization creation exactly as the API does it.
"""
import asyncio
from database_config import connect_db, disconnect_db, database
from services.organization_service import organization_service
from models import OrganizationCreate, UserCreate

async def test_api_org_creation():
    """Test the exact API flow for organization creation."""
    print("Testing API organization creation flow...")
    
    # Simulate FastAPI startup
    print("1. Connecting database (like FastAPI startup)...")
    await connect_db()
    print(f"Database connected: {database.is_connected}")
    
    # Simulate API endpoint logic
    print("2. Creating organization (like API endpoint)...")
    
    owner_email = "api_test@example.com"
    
    # Check if user exists (like API does)
    user = await organization_service.get_user_by_email(owner_email)
    if not user:
        print("Creating new user...")
        user = await organization_service.create_user(UserCreate(email=owner_email))
        print(f"Created user: {user.id}")
    else:
        print(f"Using existing user: {user.id}")
    
    # Create organization (like API does)
    organization = OrganizationCreate(
        name="API Test Org",
        slug="api-test-org",
        description="Testing API flow"
    )
    
    print("About to call create_organization...")
    org = await organization_service.create_organization(organization, user.id)
    print(f"Organization created: {org.id}")
    
    # Verify it was saved
    print("3. Verifying organization was saved...")
    orgs = await organization_service.get_organizations()
    print(f"Found {len(orgs)} organizations:")
    for o in orgs:
        print(f"  - {o.name} | {o.slug}")
    
    await disconnect_db()

if __name__ == "__main__":
    asyncio.run(test_api_org_creation())