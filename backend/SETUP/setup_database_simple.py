#!/usr/bin/env python3
"""
Simple database setup script for AutoRFP.
This script creates tables directly in the default schema without requiring extensions.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Load environment variables
load_dotenv()

async def setup_database_simple():
    """Setup the AutoRFP database tables in the default schema."""
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
        
        # Read and execute simplified SQL file
        sql_dir = Path(__file__).parent / "sql"
        tables_file = sql_dir / "03_create_tables_simple.sql"
        
        if tables_file.exists():
            print("Creating tables in default schema...")
            try:
                tables_sql = tables_file.read_text()
                await conn.execute(tables_sql)
                print("Tables created successfully")
            except Exception as tables_error:
                print(f"Tables creation failed: {tables_error}")
                print("Manual action may be required by database administrator")
                return
        
        # Verify tables were created
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'auto_rfp_%'
            ORDER BY table_name
        """)
        
        print(f"\nCreated {len(tables)} Auto_RFP tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        print("\nDatabase setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(setup_database_simple())