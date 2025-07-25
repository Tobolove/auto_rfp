"""
Qdrant vector database service for RAG-based question answering.
Handles company knowledge storage and semantic search for RFP responses.
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer

from database_config import database, get_table_name


class QdrantVectorService:
    """Service for vector storage and semantic search using Qdrant."""
    
    def __init__(self):
        # Qdrant setup
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.vector_size = 384  # all-MiniLM-L6-v2 embedding size
        
        if self.qdrant_url and self.qdrant_api_key:
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
            )
        else:
            # Use local Qdrant for development
            try:
                self.client = QdrantClient(host="localhost", port=6333)
            except:
                self.client = None
                print("Warning: Qdrant not available. Vector search will be disabled.")
        
        # Sentence transformer for embeddings
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            self.embedding_model = None
            print("Warning: Sentence transformers not available. Using mock embeddings.")
    
    async def initialize_organization_collection(self, organization_id: str) -> bool:
        """Initialize a Qdrant collection for an organization's knowledge base."""
        if not self.client:
            return False
        
        collection_name = f"org_{organization_id}"
        
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]
            
            if collection_name in existing:
                print(f"Collection {collection_name} already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            print(f"Created Qdrant collection: {collection_name}")
            return True
            
        except Exception as e:
            print(f"Failed to initialize collection {collection_name}: {e}")
            return False
    
    async def index_company_documents(self, organization_id: str, documents: List[Dict[str, Any]]) -> bool:
        """Index company documents for RAG-based responses."""
        if not self.client or not self.embedding_model:
            print("Qdrant or embedding model not available")
            return False
        
        collection_name = f"org_{organization_id}"
        
        try:
            # Ensure collection exists
            await self.initialize_organization_collection(organization_id)
            
            points = []
            for doc in documents:
                # Create chunks from document content
                chunks = self._create_text_chunks(doc["content"], chunk_size=500, overlap=50)
                
                for i, chunk in enumerate(chunks):
                    # Generate embedding
                    embedding = self.embedding_model.encode(chunk).tolist()
                    
                    # Create point
                    point_id = str(uuid.uuid4())
                    point = models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "document_id": doc["id"],
                            "document_name": doc["name"],
                            "document_type": doc.get("type", "unknown"),
                            "chunk_index": i,
                            "text": chunk,
                            "organization_id": organization_id,
                            "indexed_at": datetime.now().isoformat()
                        }
                    )
                    points.append(point)
            
            # Insert points in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
            
            print(f"Indexed {len(points)} chunks from {len(documents)} documents")
            return True
            
        except Exception as e:
            print(f"Failed to index documents: {e}")
            return False
    
    async def search_relevant_content(
        self, 
        organization_id: str, 
        query: str, 
        limit: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for relevant content to answer a question."""
        if not self.client or not self.embedding_model:
            # Return mock results for development
            return [
                {
                    "text": f"Sample relevant content for query: {query}",
                    "document_name": "Company Policy Manual",
                    "score": 0.85,
                    "document_id": "mock-doc-1"
                },
                {
                    "text": f"Additional context related to: {query}",
                    "document_name": "Technical Specifications",
                    "score": 0.78,
                    "document_id": "mock-doc-2"
                }
            ]
        
        collection_name = f"org_{organization_id}"
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search for similar vectors
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for hit in search_result:
                payload = hit.payload
                result = {
                    "text": payload.get("text", ""),
                    "document_name": payload.get("document_name", ""),
                    "document_id": payload.get("document_id", ""),
                    "document_type": payload.get("document_type", ""),
                    "score": hit.score,
                    "chunk_index": payload.get("chunk_index", 0)
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Search failed: {e}")
            # Return empty results on error
            return []
    
    def _create_text_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks for better search results."""
        if not text:
            return []
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) > 0:
                chunks.append(chunk_text.strip())
        
        return chunks
    
    async def add_company_knowledge(
        self, 
        organization_id: str, 
        content: str, 
        source: str, 
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Add a piece of company knowledge to the vector database."""
        if not self.client or not self.embedding_model:
            return False
        
        collection_name = f"org_{organization_id}"
        
        try:
            # Ensure collection exists
            await self.initialize_organization_collection(organization_id)
            
            # Create chunks
            chunks = self._create_text_chunks(content)
            
            points = []
            for i, chunk in enumerate(chunks):
                embedding = self.embedding_model.encode(chunk).tolist()
                
                payload = {
                    "text": chunk,
                    "source": source,
                    "chunk_index": i,
                    "organization_id": organization_id,
                    "added_at": datetime.now().isoformat()
                }
                
                if metadata:
                    payload.update(metadata)
                
                point = models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Insert points
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to add knowledge: {e}")
            return False
    
    async def get_collection_info(self, organization_id: str) -> Dict[str, Any]:
        """Get information about an organization's vector collection."""
        if not self.client:
            return {"status": "unavailable", "reason": "Qdrant not connected"}
        
        collection_name = f"org_{organization_id}"
        
        try:
            collection_info = self.client.get_collection(collection_name)
            return {
                "status": "active",
                "name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "points_count": collection_info.points_count
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "collection_name": collection_name
            }
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the Qdrant connection."""
        if not self.client:
            return {"status": "disconnected", "error": "Client not initialized"}
        
        try:
            collections = self.client.get_collections()
            return {
                "status": "connected",
                "collections_count": len(collections.collections),
                "collections": [c.name for c in collections.collections]
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Global service instance
qdrant_service = QdrantVectorService()