"""
Local SQLite database configuration for AutoRFP development.
"""
import os
import sqlite3
from pathlib import Path
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Local SQLite database path
DB_DIR = Path(__file__).parent / "data"
DB_DIR.mkdir(exist_ok=True)
SQLITE_DB_PATH = DB_DIR / "auto_rfp_local.db"

# Database URL for local development
LOCAL_DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"

# Database instance for async operations
database = Database(LOCAL_DATABASE_URL)

# SQLAlchemy setup for ORM
engine = create_engine(LOCAL_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Metadata for schema introspection
metadata = MetaData()

async def connect_db():
    """Connect to the local SQLite database."""
    await database.connect()
    print(f"Connected to local SQLite database: {SQLITE_DB_PATH}")

async def disconnect_db():
    """Disconnect from the local SQLite database."""
    await database.disconnect()
    print("Disconnected from local SQLite database")

def get_db():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database with tables."""
    # Create tables using SQLAlchemy
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")