#!/usr/bin/env python3
"""
Database setup script for AutoRFP.
This script safely creates the schema and tables without affecting existing data.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Load environment variables
load_dotenv()

async def setup_database():
    """Setup the AutoRFP database schema and tables."""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Parse connection URL for asyncpg
    import urllib.parse
    parsed = urllib.parse.urlparse(DATABASE_URL)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]  # Remove leading slash
        )
        
        print("Connected to PostgreSQL database")
        
        # Read and execute SQL files
        sql_dir = Path(__file__).parent / "sql"
        
        # 1. Create schema (handle permission errors gracefully)
        schema_file = sql_dir / "01_create_schema.sql"
        if schema_file.exists():
            print("Creating auto_rfp schema...")
            try:
                schema_sql = schema_file.read_text()
                await conn.execute(schema_sql)
                print("Schema created successfully")
            except Exception as schema_error:
                print(f"Schema creation failed (may already exist): {schema_error}")
                # Check if schema exists
                schema_exists = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auto_rfp')"
                )
                if schema_exists:
                    print("auto_rfp schema already exists, continuing...")
                else:
                    print("Schema does not exist and cannot be created. Please create manually:")
                    print("CREATE SCHEMA IF NOT EXISTS auto_rfp;")
        
        # 2. Create tables (handle permission errors gracefully)
        tables_file = sql_dir / "02_create_tables.sql"
        if tables_file.exists():
            print("Creating tables...")
            try:
                tables_sql = tables_file.read_text()
                await conn.execute(tables_sql)
                print("Tables created successfully")
            except Exception as tables_error:
                print(f"Tables creation failed: {tables_error}")
                print("Manual action may be required by database administrator")
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'auto_rfp'
            ORDER BY table_name
        """)
        
        print(f"\nCreated {len(tables)} tables in auto_rfp schema:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        print("\nDatabase setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database())