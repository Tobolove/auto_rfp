#!/usr/bin/env python3
"""
Test the API database connection issue.
"""
import asyncio
from database_config import database, connect_db
from services.organization_service import organization_service
from models import OrganizationCreate, UserCreate

async def test_api_simulation():
    """Simulate what happens when API calls the service."""
    print("Testing API simulation...")
    
    # This simulates the FastAPI startup
    print("1. Connecting database (simulating FastAPI startup)...")
    await connect_db()
    
    print("2. Testing service operations (simulating API calls)...")
    
    # Check if database is connected
    print(f"Database connected: {database.is_connected}")
    
    # Test the service that's imported by main.py
    try:
        # Test get_organizations (this should work with database)
        orgs = await organization_service.get_organizations()
        print(f"Found {len(orgs)} organizations via service:")
        for org in orgs:
            print(f"  - {org.name}")
            
    except Exception as e:
        print(f"Service call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_simulation())