"""
Database configuration for PostgreSQL (migrated from SQLite).
"""
import os
from pathlib import Path

from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient

# Fix OpenMP library conflict
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_qytSrWXRm0A5@ep-polished-morning-a9us695w-pooler.gwc.azure.neon.tech/neondb?sslmode=require&channel_binding=require")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

print(f"Using PostgreSQL database: {DATABASE_URL[:50]}...")

# PostgreSQL connection configuration
connect_args = {}
if "sslmode=require" in DATABASE_URL:
    connect_args = {"sslmode": "require"}

# Database type flag
USE_POSTGRESQL = True

# Database instance for async operations
database = Database(DATABASE_URL)

# SQLAlchemy setup for ORM
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Metadata for schema introspection
metadata = MetaData()

async def connect_db():
    """Connect to the PostgreSQL database."""
    await database.connect()
    print(f"Connected to PostgreSQL database")
    print(f"Is connected: {database.is_connected}")

async def disconnect_db():
    """Disconnect from the PostgreSQL database."""
    await database.disconnect()
    print(f"Disconnected from PostgreSQL database")

def get_db():
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_table_name(base_name: str) -> str:
    """Get the table name (PostgreSQL uses standard table names)."""
    return base_name

endpoint = os.getenv("AZURE_GPT_ENDPOINT")
api_key = os.getenv("AZURE_GPT_KEY")
model_name = "gpt-4.1-mini"
collection_name = "rfp_ai_collection"

# Initialize Qdrant Client
client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Load Qdrant Collection
collection_name = "rfp_ai_collection"

# Initialize Qdrant Vectorstore with Embeddings
embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=endpoint,
    openai_api_key=api_key,
    model="text-embedding-3-large-2"
)

# Initialize Qdrant Vectorstore
vectorstore = Qdrant(client, collection_name=collection_name, embeddings=embeddings)