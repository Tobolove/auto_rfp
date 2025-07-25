#!/usr/bin/env python3
"""
Test database connection and operations.
"""
import asyncio
from database_config import database, connect_db, disconnect_db, get_table_name

async def test_database():
    """Test database connection and basic operations."""
    try:
        print("Connecting to database...")
        await connect_db()
        
        # Test simple query
        org_table = get_table_name("organizations")
        print(f"Testing query on table: {org_table}")
        
        rows = await database.fetch_all(f"SELECT * FROM {org_table}")
        print(f"Found {len(rows)} organizations in database:")
        for row in rows:
            print(f"  - {row['name']} | {row['slug']}")
        
        # Test insert
        print("\nTesting insert...")
        test_org_id = "test-12345"
        insert_query = f"""
            INSERT INTO {org_table} (id, name, slug, description, created_at, updated_at)
            VALUES (:id, :name, :slug, :description, :created_at, :updated_at)
        """
        await database.execute(insert_query, {
            "id": test_org_id,
            "name": "Test Insert Org",
            "slug": "test-insert-org",
            "description": "Testing direct insert",
            "created_at": "2025-07-24T17:20:00",
            "updated_at": "2025-07-24T17:20:00"
        })
        print("Insert successful!")
        
        # Verify insert
        rows = await database.fetch_all(f"SELECT * FROM {org_table}")
        print(f"After insert: {len(rows)} organizations")
        
        await disconnect_db()
        
    except Exception as e:
        print(f"Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database())