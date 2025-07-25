#!/usr/bin/env python3
"""
Local SQLite database setup script for AutoRFP.
This script creates tables for local development and testing.
"""
import asyncio
import sqlite3
from pathlib import Path

async def setup_local_database():
    """Setup the local SQLite database with all tables."""
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Database file path
    db_path = data_dir / "auto_rfp_local.db"
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Connected to local SQLite database: {db_path}")
        
        # Read and execute SQL file
        sql_dir = Path(__file__).parent / "sql"
        tables_file = sql_dir / "04_create_tables_sqlite.sql"
        
        if tables_file.exists():
            print("Creating tables in local SQLite database...")
            try:
                tables_sql = tables_file.read_text()
                cursor.executescript(tables_sql)
                conn.commit()
                print("Tables created successfully")
            except Exception as tables_error:
                print(f"Tables creation failed: {tables_error}")
                return
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        tables = cursor.fetchall()
        
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Add some sample data for testing
        print("\nAdding sample data...")
        
        # Sample organization
        cursor.execute("""
            INSERT OR IGNORE INTO organizations (name, slug, description) 
            VALUES ('Test Company', 'test-company', 'A test organization for development')
        """)
        
        # Sample user
        cursor.execute("""
            INSERT OR IGNORE INTO users (email, name) 
            VALUES ('test@example.com', 'Test User')
        """)
        
        conn.commit()
        
        # Verify sample data
        cursor.execute("SELECT COUNT(*) FROM organizations")
        org_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"Sample data added: {org_count} organizations, {user_count} users")
        
        conn.close()
        print("\nLocal database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up local database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_local_database())