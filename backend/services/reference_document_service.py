"""
Reference Document Service for managing company knowledge base documents
Handles upload, vectorization, and intelligent filtering for RAG-based RFP responses
"""
import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path

# File processing
import fitz  # PyMuPDF for PDF processing
from docx import Document as DocxDocument
import pandas as pd
from io import BytesIO

# Azure services
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential

# Vector database
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, VectorParams, Distance, Filter, FieldCondition, 
    MatchValue, MatchAny, SearchRequest
)

# LangChain for embeddings
from langchain_openai import AzureOpenAIEmbeddings
from sentence_transformers import SentenceTransformer

# Database and models
from database_config import database, get_table_name
from models_reference import (
    ReferenceDocumentMetadata, ReferenceDocumentCreate, ReferenceDocumentUpdate,
    ReferenceDocumentFilter, DocumentUploadRequest, DocumentUploadResponse,
    SmartFilterRequest, SmartFilterResponse, DocumentType, IndustryTag, CapabilityTag
)

logger = logging.getLogger(__name__)


class ReferenceDocumentService:
    """
    Service for managing reference documents in the company knowledge base.
    
    Features:
    - Upload and process various document formats (PDF, DOCX, TXT, Excel)
    - Extract text using Azure Document Intelligence
    - Vectorize content with metadata tagging
    - Store in Qdrant vector database with smart filtering
    - Integrate with RAG system for RFP response generation
    """
    
    def __init__(self):
        """Initialize the reference document service."""
        # Qdrant Configuration
        self.qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_PROD_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_PROD_API_KEY")
        self.collection_name = "RFP_AI_Collection"  # Same collection as RAG system
        
        # Azure Configuration
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2024-10-21")
        
        # Azure Document Intelligence
        self.doc_intelligence_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.doc_intelligence_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        # Storage
        self.storage_base_path = os.getenv("REFERENCE_DOCS_PATH", "./backend/storage/reference_docs")
        os.makedirs(self.storage_base_path, exist_ok=True)
        
        # Initialize clients
        self._initialize_clients()
        
        # Processing configuration
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        
    def _initialize_clients(self):
        """Initialize Azure and Qdrant clients."""
        try:
            # Qdrant Client
            if self.qdrant_url and self.qdrant_api_key:
                self.qdrant_client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key
                )
                print(f"✅ Qdrant client initialized for {self.collection_name}")
            else:
                self.qdrant_client = None
                print("⚠️ Qdrant not configured")
            
            # Azure OpenAI Embeddings
            if self.azure_endpoint and self.azure_api_key:
                self.embeddings = AzureOpenAIEmbeddings(
                    azure_endpoint=self.azure_endpoint,
                    api_key=self.azure_api_key,
                    api_version=self.azure_api_version,
                    model="text-embedding-3-large"
                )
                print("✅ Azure OpenAI embeddings initialized")
            else:
                # Fallback to local embeddings
                self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
                print("⚠️ Using local embeddings (SentenceTransformers)")
            
            # Azure Document Intelligence
            if self.doc_intelligence_endpoint and self.doc_intelligence_key:
                self.doc_client = DocumentIntelligenceClient(
                    endpoint=self.doc_intelligence_endpoint,
                    credential=AzureKeyCredential(self.doc_intelligence_key)
                )
                print("✅ Azure Document Intelligence initialized")
            else:
                self.doc_client = None
                print("⚠️ Azure Document Intelligence not configured")
                
        except Exception as e:
            print(f"❌ Error initializing clients: {e}")
            self.qdrant_client = None
            self.embeddings = None
            self.doc_client = None
    
    async def upload_document(
        self, 
        file_content: bytes, 
        metadata: ReferenceDocumentCreate
    ) -> DocumentUploadResponse:
        """
        Upload and process a reference document.
        
        Args:
            file_content: Binary content of the document
            metadata: Document metadata and classification
            
        Returns:
            Upload response with success status and document ID
        """
        try:
            print(f"📤 Uploading reference document: {metadata.filename}")
            
            # Validate file size
            if len(file_content) > self.max_file_size:
                return DocumentUploadResponse(
                    success=False,
                    document_id="",
                    message=f"File too large. Maximum size is {self.max_file_size / 1024 / 1024:.1f}MB"
                )
            
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Save file to storage
            file_path = await self._save_file(document_id, metadata.filename, file_content)
            
            # Extract text content
            text_content = await self._extract_text(file_path, file_content)
            if not text_content or len(text_content.strip()) < 50:
                return DocumentUploadResponse(
                    success=False,
                    document_id="",
                    message="Could not extract meaningful text from document"
                )
            
            # Create metadata object
            doc_metadata = ReferenceDocumentMetadata(
                document_id=document_id,
                filename=metadata.filename,
                original_name=metadata.original_name,
                document_type=metadata.document_type,
                industry_tags=metadata.industry_tags,
                capability_tags=metadata.capability_tags,
                project_size=metadata.project_size,
                geographic_scope=metadata.geographic_scope,
                organization_id=metadata.organization_id,
                confidence_level=metadata.confidence_level,
                custom_tags=metadata.custom_tags,
                description=metadata.description,
                keywords=metadata.keywords,
                upload_date=datetime.now(),
                is_active=True
            )
            
            # Save to database
            await self._save_to_database(doc_metadata, file_path, text_content)
            
            # Vectorize and upload to Qdrant
            vector_id = None
            if self.qdrant_client:
                vector_id = await self._vectorize_and_upload(text_content, doc_metadata)
            
            return DocumentUploadResponse(
                success=True,
                document_id=document_id,
                message="Document uploaded and processed successfully",
                metadata=doc_metadata,
                vector_id=vector_id
            )
            
        except Exception as e:
            print(f"❌ Error uploading document: {e}")
            return DocumentUploadResponse(
                success=False,
                document_id="",
                message=f"Upload failed: {str(e)}"
            )
    
    async def _save_file(self, document_id: str, filename: str, content: bytes) -> str:
        """Save file to storage and return file path."""
        # Create organization subdirectory if needed
        file_ext = Path(filename).suffix
        file_path = os.path.join(self.storage_base_path, f"{document_id}{file_ext}")
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    async def _extract_text(self, file_path: str, file_content: bytes) -> str:
        """Extract text from various document formats."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.pdf':
                return await self._extract_text_pdf(file_content)
            elif file_ext in ['.docx', '.doc']:
                return await self._extract_text_docx(file_content)
            elif file_ext in ['.txt', '.md']:
                return file_content.decode('utf-8', errors='ignore')
            elif file_ext in ['.xlsx', '.xls']:
                return await self._extract_text_excel(file_content)
            else:
                # Try Azure Document Intelligence for unknown formats
                if self.doc_client:
                    return await self._extract_text_azure(file_content)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")
                    
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            raise
    
    async def _extract_text_pdf(self, content: bytes) -> str:
        """Extract text from PDF using PyMuPDF."""
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text_parts = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")
            
            doc.close()
            return "\n\n".join(text_parts)
            
        except Exception as e:
            print(f"❌ PDF extraction error: {e}")
            # Fallback to Azure Document Intelligence
            if self.doc_client:
                return await self._extract_text_azure(content)
            raise
    
    async def _extract_text_docx(self, content: bytes) -> str:
        """Extract text from DOCX files."""
        try:
            doc = DocxDocument(BytesIO(content))
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            print(f"❌ DOCX extraction error: {e}")
            raise
    
    async def _extract_text_excel(self, content: bytes) -> str:
        """Extract text from Excel files."""
        try:
            # Read all sheets
            excel_data = pd.read_excel(BytesIO(content), sheet_name=None)
            text_parts = []
            
            for sheet_name, df in excel_data.items():
                text_parts.append(f"[Sheet: {sheet_name}]")
                # Convert dataframe to text representation
                text_parts.append(df.to_string(index=False))
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            print(f"❌ Excel extraction error: {e}")
            raise
    
    async def _extract_text_azure(self, content: bytes) -> str:
        """Extract text using Azure Document Intelligence."""
        try:
            # Azure Document Intelligence implementation
            # Note: This is a simplified version - full implementation would handle pagination
            poller = self.doc_client.begin_analyze_document(
                "prebuilt-read", 
                content
            )
            result = poller.result()
            
            return result.content if result.content else ""
            
        except Exception as e:
            print(f"❌ Azure Document Intelligence error: {e}")
            raise
    
    async def _save_to_database(
        self, 
        metadata: ReferenceDocumentMetadata, 
        file_path: str, 
        text_content: str
    ):
        """Save document metadata to database."""
        try:
            # Create table if it doesn't exist
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS reference_documents (
                    id VARCHAR(36) PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    original_name VARCHAR(255) NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    industry_tags TEXT,
                    capability_tags TEXT,
                    project_size VARCHAR(20),
                    geographic_scope VARCHAR(20),
                    organization_id VARCHAR(36) NOT NULL,
                    confidence_level VARCHAR(10) NOT NULL,
                    custom_tags TEXT,
                    description TEXT,
                    keywords TEXT,
                    file_path VARCHAR(500) NOT NULL,
                    content_length INTEGER,
                    upload_date DATETIME NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            await database.execute(create_table_query)
            
            # Insert document record
            insert_query = f"""
                INSERT INTO reference_documents (
                    id, filename, original_name, document_type, industry_tags, capability_tags,
                    project_size, geographic_scope, organization_id, confidence_level,
                    custom_tags, description, keywords, file_path, content_length,
                    upload_date, is_active
                ) VALUES (
                    :id, :filename, :original_name, :document_type, :industry_tags, :capability_tags,
                    :project_size, :geographic_scope, :organization_id, :confidence_level,
                    :custom_tags, :description, :keywords, :file_path, :content_length,
                    :upload_date, :is_active
                )
            """
            
            await database.execute(insert_query, {
                "id": metadata.document_id,
                "filename": metadata.filename,
                "original_name": metadata.original_name,
                "document_type": metadata.document_type.value,
                "industry_tags": ",".join([tag.value for tag in metadata.industry_tags]),
                "capability_tags": ",".join([tag.value for tag in metadata.capability_tags]),
                "project_size": metadata.project_size.value if metadata.project_size else None,
                "geographic_scope": metadata.geographic_scope.value if metadata.geographic_scope else None,
                "organization_id": metadata.organization_id,
                "confidence_level": metadata.confidence_level.value,
                "custom_tags": ",".join(metadata.custom_tags),
                "description": metadata.description,
                "keywords": ",".join(metadata.keywords),
                "file_path": file_path,
                "content_length": len(text_content),
                "upload_date": metadata.upload_date,
                "is_active": metadata.is_active
            })
            
            print(f"✅ Document metadata saved to database: {metadata.document_id}")
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            raise
    
    async def _vectorize_and_upload(
        self, 
        text_content: str, 
        metadata: ReferenceDocumentMetadata
    ) -> str:
        """Vectorize document content and upload to Qdrant."""
        try:
            # Split content into chunks
            chunks = self._create_chunks(text_content)
            
            # Create vectors for each chunk
            points = []
            for i, chunk in enumerate(chunks):
                # Generate embedding
                if hasattr(self.embeddings, 'embed_query'):
                    vector = self.embeddings.embed_query(chunk)
                else:
                    vector = self.embeddings.encode([chunk])[0].tolist()
                
                # Create Qdrant point with metadata
                point_id = f"{metadata.document_id}_chunk_{i}"
                
                # Prepare payload with all metadata for filtering
                payload = {
                    "content": chunk,
                    "document_id": metadata.document_id,
                    "filename": metadata.filename,
                    "document_type": metadata.document_type.value,
                    "industry_tags": [tag.value for tag in metadata.industry_tags],
                    "capability_tags": [tag.value for tag in metadata.capability_tags],
                    "organization_id": metadata.organization_id,
                    "confidence_level": metadata.confidence_level.value,
                    "is_active": metadata.is_active,
                    "upload_date": metadata.upload_date.isoformat(),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "keywords": metadata.keywords,
                    "custom_tags": metadata.custom_tags
                }
                
                # Add optional fields
                if metadata.project_size:
                    payload["project_size"] = metadata.project_size.value
                if metadata.geographic_scope:
                    payload["geographic_scope"] = metadata.geographic_scope.value
                if metadata.description:
                    payload["description"] = metadata.description
                
                points.append(PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                ))
            
            # Upload to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            
            print(f"✅ Document vectorized and uploaded: {len(chunks)} chunks")
            return f"{metadata.document_id}_chunks"
            
        except Exception as e:
            print(f"❌ Error vectorizing document: {e}")
            raise
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks for vectorization."""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                # Find a good break point (sentence boundary)
                break_point = text.rfind('.', start, end)
                if break_point == -1:
                    break_point = text.rfind(' ', start, end)
                if break_point != -1 and break_point > start:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap if end < len(text) else end
        
        return chunks
    
    async def get_organization_documents(
        self, 
        organization_id: str,
        filter_params: Optional[ReferenceDocumentFilter] = None
    ) -> List[Dict[str, Any]]:
        """Get all reference documents for an organization."""
        try:
            query = "SELECT * FROM reference_documents WHERE organization_id = :org_id"
            params = {"org_id": organization_id}
            
            # Add filters
            if filter_params:
                if filter_params.document_types:
                    doc_types = [dt.value for dt in filter_params.document_types]
                    query += f" AND document_type IN ({','.join(['?' for _ in doc_types])})"
                    params.update({f"dt_{i}": dt for i, dt in enumerate(doc_types)})
                
                if filter_params.is_active is not None:
                    query += " AND is_active = :is_active"
                    params["is_active"] = filter_params.is_active
            
            query += " ORDER BY upload_date DESC"
            
            rows = await database.fetch_all(query, params)
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"❌ Error fetching documents: {e}")
            return []
    
    async def delete_document(self, document_id: str, organization_id: str) -> bool:
        """Delete a reference document and its vectors."""
        try:
            # Remove from database
            query = "DELETE FROM reference_documents WHERE id = :doc_id AND organization_id = :org_id"
            result = await database.execute(query, {
                "doc_id": document_id,
                "org_id": organization_id
            })
            
            # Remove from Qdrant (all chunks)
            if self.qdrant_client:
                # Get all point IDs for this document
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
                
                # Delete points matching the filter
                self.qdrant_client.delete(
                    collection_name=self.collection_name,
                    points_selector=search_filter
                )
            
            # Delete file from storage
            try:
                file_query = "SELECT file_path FROM reference_documents WHERE id = :doc_id"
                file_row = await database.fetch_one(file_query, {"doc_id": document_id})
                if file_row and os.path.exists(file_row['file_path']):
                    os.remove(file_row['file_path'])
            except Exception as e:
                print(f"⚠️ Could not delete file: {e}")
            
            print(f"✅ Document deleted: {document_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting document: {e}")
            return False


# Global service instance
reference_document_service = ReferenceDocumentService()