"""
Database configuration and connection setup for AutoRFP.
"""
import os
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Database instance for async operations
database = Database(DATABASE_URL)

# SQLAlchemy setup for ORM (if needed)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Metadata for schema introspection
metadata = MetaData(schema="auto_rfp")

async def connect_db():
    """Connect to the database."""
    await database.connect()
    print("✅ Connected to PostgreSQL database")

async def disconnect_db():
    """Disconnect from the database."""
    await database.disconnect()
    print("✅ Disconnected from PostgreSQL database")

def get_db():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()