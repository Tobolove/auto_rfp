"""
Qdrant Vector Database Service for semantic search and document retrieval.
Replaces LlamaCloud vector search capabilities.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from uuid import UUID
import json
from datetime import datetime

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct, Filter, FieldCondition, 
    MatchValue, SearchRequest, CollectionInfo, PayloadSchemaType
)
from qdrant_client.http.exceptions import UnexpectedResponse
import openai
from sentence_transformers import SentenceTransformer

from models import Document, Question, Answer, Source

logger = logging.getLogger(__name__)

class QdrantVectorService:
    """
    Qdrant vector database service for semantic search and document retrieval.
    
    Features:
    - Document embedding and storage
    - Semantic search across documents
    - Context retrieval for AI responses
    - Multi-tenant collections per organization
    - Hybrid search (vector + keyword filtering)
    """
    
    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: Optional[str] = None,
        openai_client: Optional[openai.AsyncOpenAI] = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize Qdrant Vector Service.
        
        Args:
            qdrant_url: Qdrant server URL
            qdrant_api_key: API key for Qdrant authentication
            openai_client: OpenAI client for embeddings (fallback)
            embedding_model: SentenceTransformers model for embeddings
        """
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.openai_client = openai_client
        self.embedding_model_name = embedding_model
        
        # Initialize clients
        self.qdrant_client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key,
            timeout=30
        )
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer(embedding_model)
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model: {embedding_model} (dim: {self.embedding_dimension})")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer model: {e}")
            self.embedding_model = None
            self.embedding_dimension = 1536  # OpenAI default
    
    async def create_organization_collection(self, organization_id: UUID) -> bool:
        """
        Create a dedicated collection for an organization.
        
        Args:
            organization_id: Organization identifier
        
        Returns:
            True if collection was created successfully
        """
        collection_name = self._get_collection_name(organization_id)
        
        try:
            # Check if collection already exists
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists")
                return True
            except UnexpectedResponse:
                pass  # Collection doesn't exist, create it
            
            # Create collection with appropriate vector configuration
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
            # Create payload indexes for efficient filtering
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="project_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="document_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            self.qdrant_client.create_payload_index(
                collection_name=collection_name,
                field_name="content_type",
                field_schema=PayloadSchemaType.KEYWORD
            )
            
            logger.info(f"Created collection {collection_name} with vector dimension {self.embedding_dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {str(e)}")
            return False
    
    async def index_document(
        self,
        document: Document,
        parsed_content: Dict[str, Any],
        organization_id: UUID,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> bool:
        """
        Index a document in the vector database.
        
        Args:
            document: Document metadata
            parsed_content: Parsed document content from Azure Document Intelligence
            organization_id: Organization identifier
            chunk_size: Size of text chunks for embedding
            chunk_overlap: Overlap between chunks
        
        Returns:
            True if document was indexed successfully
        """
        collection_name = self._get_collection_name(organization_id)
        
        try:
            # Ensure collection exists
            await self.create_organization_collection(organization_id)
            
            # Extract and chunk content
            chunks = await self._create_document_chunks(
                parsed_content, chunk_size, chunk_overlap
            )
            
            # Generate embeddings for chunks
            embeddings = await self._generate_embeddings([chunk["text"] for chunk in chunks])
            
            # Prepare points for insertion
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = f"{document.id}_{i}"
                
                payload = {
                    "document_id": str(document.id),
                    "project_id": str(document.project_id),
                    "organization_id": str(organization_id),
                    "document_name": document.name,
                    "chunk_index": i,
                    "content_type": "document_chunk",
                    "text": chunk["text"],
                    "page_number": chunk.get("page_number", 1),
                    "section_title": chunk.get("section_title", ""),
                    "metadata": {
                        "file_type": document.file_type,
                        "file_size": document.file_size,
                        "indexed_at": datetime.now().isoformat(),
                        "chunk_size": len(chunk["text"]),
                        **chunk.get("metadata", {})
                    }
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                    payload=payload
                )
                points.append(point)
            
            # Insert points in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
            
            logger.info(f"Indexed document {document.id} with {len(points)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {str(e)}")
            return False
    
    async def search_similar_content(
        self,
        query: str,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using semantic search.
        
        Args:
            query: Search query
            organization_id: Organization identifier
            project_id: Optional project filter
            limit: Maximum number of results
            score_threshold: Minimum similarity score
        
        Returns:
            List of similar content chunks with metadata
        """
        collection_name = self._get_collection_name(organization_id)
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            if not query_embedding:
                return []
            
            # Prepare search filters
            must_conditions = [
                FieldCondition(
                    key="organization_id",
                    match=MatchValue(value=str(organization_id))
                )
            ]
            
            if project_id:
                must_conditions.append(
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=str(project_id))
                    )
                )
            
            search_filter = Filter(must=must_conditions) if must_conditions else None
            
            # Perform vector search
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding[0].tolist() if isinstance(query_embedding[0], np.ndarray) else query_embedding[0],
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                formatted_result = {
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "document_id": result.payload.get("document_id"),
                    "document_name": result.payload.get("document_name"),
                    "page_number": result.payload.get("page_number"),
                    "section_title": result.payload.get("section_title"),
                    "chunk_index": result.payload.get("chunk_index"),
                    "metadata": result.payload.get("metadata", {})
                }
                results.append(formatted_result)
            
            logger.info(f"Found {len(results)} similar content chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for similar content: {str(e)}")
            return []
    
    async def get_context_for_question(
        self,
        question: str,
        organization_id: UUID,
        project_id: UUID,
        max_context_length: int = 4000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get relevant context for answering a question.
        
        Args:
            question: Question text
            organization_id: Organization identifier
            project_id: Project identifier
            max_context_length: Maximum context length in characters
        
        Returns:
            Tuple of (context_text, source_chunks)
        """
        try:
            # Search for relevant content
            similar_chunks = await self.search_similar_content(
                query=question,
                organization_id=organization_id,
                project_id=project_id,
                limit=20,
                score_threshold=0.6
            )
            
            if not similar_chunks:
                return "", []
            
            # Combine chunks into context, respecting length limit
            context_parts = []
            total_length = 0
            sources = []
            
            for chunk in similar_chunks:
                chunk_text = chunk["text"]
                if total_length + len(chunk_text) > max_context_length:
                    break
                
                context_parts.append(f"[Document: {chunk['document_name']}, Page: {chunk['page_number']}]\n{chunk_text}")
                total_length += len(chunk_text)
                
                # Track source information
                source_info = {
                    "document_id": chunk["document_id"],
                    "document_name": chunk["document_name"],
                    "page_number": chunk["page_number"],
                    "section_title": chunk["section_title"],
                    "relevance_score": chunk["score"],
                    "text_excerpt": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
                }
                sources.append(source_info)
            
            context_text = "\n\n".join(context_parts)
            logger.info(f"Generated context with {len(context_parts)} chunks ({total_length} characters)")
            
            return context_text, sources
            
        except Exception as e:
            logger.error(f"Error getting context for question: {str(e)}")
            return "", []
    
    async def remove_document(self, document_id: UUID, organization_id: UUID) -> bool:
        """
        Remove all chunks for a document from the vector database.
        
        Args:
            document_id: Document identifier
            organization_id: Organization identifier
        
        Returns:
            True if document was removed successfully
        """
        collection_name = self._get_collection_name(organization_id)
        
        try:
            # Delete all points for this document
            self.qdrant_client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=str(document_id))
                        )
                    ]
                )
            )
            
            logger.info(f"Removed document {document_id} from vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document {document_id}: {str(e)}")
            return False
    
    async def create_quote_collection(self) -> bool:
        """
        Create a dedicated collection for RFP quotes and responses.
        
        Returns:
            True if collection was created successfully
        """
        collection_name = "quote_collection"
        
        try:
            # Check if collection already exists
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"Collection {collection_name} already exists")
                return True
            except UnexpectedResponse:
                pass  # Collection doesn't exist, create it
            
            # Create collection with appropriate vector configuration
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
            # Create payload indexes for efficient filtering
            payload_indexes = [
                ("organization_id", PayloadSchemaType.KEYWORD),
                ("project_id", PayloadSchemaType.KEYWORD),
                ("quote_id", PayloadSchemaType.KEYWORD),
                ("quote_type", PayloadSchemaType.KEYWORD),  # "question", "answer", "source"
                ("question_id", PayloadSchemaType.KEYWORD),
                ("answer_id", PayloadSchemaType.KEYWORD),
                ("source_type", PayloadSchemaType.KEYWORD),
                ("created_date", PayloadSchemaType.DATETIME),
                ("relevance_score", PayloadSchemaType.FLOAT),
                ("is_final", PayloadSchemaType.BOOL),
                ("section_category", PayloadSchemaType.KEYWORD)
            ]
            
            for field_name, field_schema in payload_indexes:
                try:
                    self.qdrant_client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_schema
                    )
                except Exception as e:
                    logger.warning(f"Could not create index for {field_name}: {str(e)}")
            
            logger.info(f"Created quote collection {collection_name} with vector dimension {self.embedding_dimension}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating quote collection {collection_name}: {str(e)}")
            return False
    
    async def index_rfp_quote(
        self,
        quote_data: Dict[str, Any],
        organization_id: UUID,
        project_id: UUID,
        quote_type: str = "complete_quote"
    ) -> bool:
        """
        Index RFP quote data in the quote collection.
        
        Args:
            quote_data: Complete quote data including questions, answers, and sources
            organization_id: Organization identifier
            project_id: Project identifier
            quote_type: Type of quote data ("complete_quote", "question", "answer", "source")
        
        Returns:
            True if quote was indexed successfully
        """
        collection_name = "quote_collection"
        
        try:
            # Ensure collection exists
            await self.create_quote_collection()
            
            points = []
            
            # Index complete quote overview
            if quote_type == "complete_quote":
                quote_overview = self._create_quote_overview(quote_data)
                overview_embedding = await self._generate_embeddings([quote_overview])
                
                if overview_embedding:
                    point_id = f"quote_{project_id}_{datetime.now().timestamp()}"
                    
                    payload = {
                        "organization_id": str(organization_id),
                        "project_id": str(project_id),
                        "quote_id": point_id,
                        "quote_type": "complete_quote",
                        "text": quote_overview,
                        "created_date": datetime.now().isoformat(),
                        "is_final": True,
                        "metadata": {
                            "total_questions": len(quote_data.get("questions", [])),
                            "total_answers": len(quote_data.get("answers", [])),
                            "completion_rate": quote_data.get("completion_rate", 0.0),
                            "quote_version": quote_data.get("version", "1.0")
                        }
                    }
                    
                    point = PointStruct(
                        id=point_id,
                        vector=overview_embedding[0].tolist() if isinstance(overview_embedding[0], np.ndarray) else overview_embedding[0],
                        payload=payload
                    )
                    points.append(point)
            
            # Index individual questions
            for question in quote_data.get("questions", []):
                question_embedding = await self._generate_embeddings([question.get("text", "")])
                
                if question_embedding:
                    point_id = f"question_{question.get('id', '')}_{project_id}"
                    
                    payload = {
                        "organization_id": str(organization_id),
                        "project_id": str(project_id),
                        "question_id": str(question.get("id", "")),
                        "quote_type": "question",
                        "text": question.get("text", ""),
                        "section_category": question.get("section", ""),
                        "created_date": datetime.now().isoformat(),
                        "metadata": {
                            "question_type": question.get("type", ""),
                            "required": question.get("required", False),
                            "section": question.get("section", ""),
                            "page_number": question.get("page_number", 1)
                        }
                    }
                    
                    point = PointStruct(
                        id=point_id,
                        vector=question_embedding[0].tolist() if isinstance(question_embedding[0], np.ndarray) else question_embedding[0],
                        payload=payload
                    )
                    points.append(point)
            
            # Index answers with sources
            for answer in quote_data.get("answers", []):
                answer_text = answer.get("text", "")
                if answer_text:
                    answer_embedding = await self._generate_embeddings([answer_text])
                    
                    if answer_embedding:
                        point_id = f"answer_{answer.get('id', '')}_{project_id}"
                        
                        # Combine sources information
                        sources_info = []
                        for source in answer.get("sources", []):
                            sources_info.append({
                                "document_name": source.get("document_name", ""),
                                "page_number": source.get("page_number", 1),
                                "relevance_score": source.get("relevance_score", 0.0)
                            })
                        
                        payload = {
                            "organization_id": str(organization_id),
                            "project_id": str(project_id),
                            "answer_id": str(answer.get("id", "")),
                            "question_id": str(answer.get("question_id", "")),
                            "quote_type": "answer",
                            "text": answer_text,
                            "created_date": datetime.now().isoformat(),
                            "relevance_score": answer.get("confidence_score", 0.0),
                            "is_final": answer.get("is_final", False),
                            "metadata": {
                                "confidence_score": answer.get("confidence_score", 0.0),
                                "sources_count": len(sources_info),
                                "sources": sources_info,
                                "answer_type": answer.get("type", "generated")
                            }
                        }
                        
                        point = PointStruct(
                            id=point_id,
                            vector=answer_embedding[0].tolist() if isinstance(answer_embedding[0], np.ndarray) else answer_embedding[0],
                            payload=payload
                        )
                        points.append(point)
            
            # Insert points in batches
            if points:
                batch_size = 100
                for i in range(0, len(points), batch_size):
                    batch = points[i:i + batch_size]
                    self.qdrant_client.upsert(
                        collection_name=collection_name,
                        points=batch
                    )
                
                logger.info(f"Indexed quote with {len(points)} components for project {project_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error indexing RFP quote: {str(e)}")
            return False
    
    async def search_similar_quotes(
        self,
        query: str,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        quote_type: Optional[str] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar quotes, questions, or answers.
        
        Args:
            query: Search query
            organization_id: Organization identifier
            project_id: Optional project filter
            quote_type: Optional filter by quote type ("question", "answer", "complete_quote")
            limit: Maximum number of results
            score_threshold: Minimum similarity score
        
        Returns:
            List of similar quote components with metadata
        """
        collection_name = "quote_collection"
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            if not query_embedding:
                return []
            
            # Prepare search filters
            must_conditions = [
                FieldCondition(
                    key="organization_id",
                    match=MatchValue(value=str(organization_id))
                )
            ]
            
            if project_id:
                must_conditions.append(
                    FieldCondition(
                        key="project_id",
                        match=MatchValue(value=str(project_id))
                    )
                )
            
            if quote_type:
                must_conditions.append(
                    FieldCondition(
                        key="quote_type",
                        match=MatchValue(value=quote_type)
                    )
                )
            
            search_filter = Filter(must=must_conditions) if must_conditions else None
            
            # Perform vector search
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding[0].tolist() if isinstance(query_embedding[0], np.ndarray) else query_embedding[0],
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            results = []
            for result in search_results:
                formatted_result = {
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "quote_type": result.payload.get("quote_type", ""),
                    "project_id": result.payload.get("project_id"),
                    "question_id": result.payload.get("question_id"),
                    "answer_id": result.payload.get("answer_id"),
                    "section_category": result.payload.get("section_category"),
                    "relevance_score": result.payload.get("relevance_score"),
                    "is_final": result.payload.get("is_final", False),
                    "created_date": result.payload.get("created_date"),
                    "metadata": result.payload.get("metadata", {})
                }
                results.append(formatted_result)
            
            logger.info(f"Found {len(results)} similar quote components for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching for similar quotes: {str(e)}")
            return []

    async def get_collection_stats(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for an organization's collection.
        
        Args:
            organization_id: Organization identifier
        
        Returns:
            Collection statistics
        """
        collection_name = self._get_collection_name(organization_id)
        
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
            
            # Count documents
            scroll_result = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=1,
                with_payload=True
            )
            
            total_points = collection_info.points_count
            
            return {
                "collection_name": collection_name,
                "total_chunks": total_points,
                "vector_dimension": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "status": collection_info.status.value
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats for organization {organization_id}: {str(e)}")
            return {}
    
    async def get_quote_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the quote collection.
        
        Returns:
            Quote collection statistics
        """
        collection_name = "quote_collection"
        
        try:
            collection_info = self.qdrant_client.get_collection(collection_name)
            
            # Count different types of quotes
            quote_types = ["complete_quote", "question", "answer"]
            type_counts = {}
            
            for quote_type in quote_types:
                scroll_result = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="quote_type",
                                match=MatchValue(value=quote_type)
                            )
                        ]
                    ),
                    limit=10000,  # Get count
                    with_payload=False
                )
                type_counts[quote_type] = len(scroll_result[0])
            
            total_points = collection_info.points_count
            
            return {
                "collection_name": collection_name,
                "total_points": total_points,
                "quote_types": type_counts,
                "vector_dimension": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.value,
                "status": collection_info.status.value
            }
            
        except Exception as e:
            logger.error(f"Error getting quote collection stats: {str(e)}")
            return {}
    
    def _create_quote_overview(self, quote_data: Dict[str, Any]) -> str:
        """Create a comprehensive overview text for a complete quote."""
        overview_parts = []
        
        # Project information
        project_info = quote_data.get("project_info", {})
        if project_info:
            overview_parts.append(f"RFP Project: {project_info.get('name', 'Unnamed Project')}")
            overview_parts.append(f"Description: {project_info.get('description', '')}")
        
        # Summary statistics
        questions = quote_data.get("questions", [])
        answers = quote_data.get("answers", [])
        
        overview_parts.append(f"Total Questions: {len(questions)}")
        overview_parts.append(f"Total Answers: {len(answers)}")
        
        # Completion rate
        completion_rate = quote_data.get("completion_rate", 0.0)
        overview_parts.append(f"Completion Rate: {completion_rate:.1%}")
        
        # Key sections
        sections = set()
        for question in questions:
            section = question.get("section", "")
            if section:
                sections.add(section)
        
        if sections:
            overview_parts.append(f"Covered Sections: {', '.join(sorted(sections))}")
        
        # Sample questions and answers (first few)
        if questions:
            overview_parts.append("\nKey Questions:")
            for i, question in enumerate(questions[:3]):
                overview_parts.append(f"- {question.get('text', '')}")
        
        if answers:
            overview_parts.append("\nSample Answers:")
            for i, answer in enumerate(answers[:2]):
                answer_text = answer.get('text', '')
                if len(answer_text) > 200:
                    answer_text = answer_text[:200] + "..."
                overview_parts.append(f"- {answer_text}")
        
        return "\n".join(overview_parts)
    
    def _get_collection_name(self, organization_id: UUID) -> str:
        """Get collection name for an organization."""
        return f"org_{str(organization_id).replace('-', '_')}"
    
    async def _create_document_chunks(
        self,
        parsed_content: Dict[str, Any],
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Create chunks from parsed document content."""
        chunks = []
        
        # Process sections
        for section in parsed_content.get("sections", []):
            section_text = section.get("content", "")
            if not section_text.strip():
                continue
            
            # Split section into chunks
            section_chunks = self._split_text_into_chunks(
                section_text, chunk_size, chunk_overlap
            )
            
            for i, chunk_text in enumerate(section_chunks):
                chunk = {
                    "text": chunk_text,
                    "page_number": section.get("page_number", 1),
                    "section_title": section.get("title", ""),
                    "metadata": {
                        "section_index": i,
                        "is_table": False
                    }
                }
                chunks.append(chunk)
        
        # Process tables separately
        for table in parsed_content.get("tables", []):
            table_content = table.get("content", "")
            if not table_content.strip():
                continue
            
            chunk = {
                "text": f"[TABLE]\n{table_content}",
                "page_number": table.get("bounding_regions", [{}])[0].get("page_number", 1),
                "section_title": "Table Data",
                "metadata": {
                    "is_table": True,
                    "row_count": table.get("row_count", 0),
                    "column_count": table.get("column_count", 0)
                }
            }
            chunks.append(chunk)
        
        # If no sections found, use full content
        if not chunks and parsed_content.get("content"):
            full_content = parsed_content["content"]
            content_chunks = self._split_text_into_chunks(
                full_content, chunk_size, chunk_overlap
            )
            
            for i, chunk_text in enumerate(content_chunks):
                chunk = {
                    "text": chunk_text,
                    "page_number": 1,
                    "section_title": "Document Content",
                    "metadata": {"chunk_index": i}
                }
                chunks.append(chunk)
        
        return chunks
    
    def _split_text_into_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                last_sentence = text.rfind('.', start, end)
                if last_sentence > start + chunk_size - 100:
                    end = last_sentence + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - chunk_overlap if end < len(text) else len(text)
        
        return chunks
    
    async def _generate_embeddings(self, texts: List[str]) -> List[Union[np.ndarray, List[float]]]:
        """Generate embeddings for a list of texts."""
        try:
            if self.embedding_model:
                # Use SentenceTransformers
                embeddings = self.embedding_model.encode(texts)
                return embeddings
            elif self.openai_client:
                # Fallback to OpenAI embeddings
                response = await self.openai_client.embeddings.create(
                    input=texts,
                    model="text-embedding-3-small"
                )
                return [item.embedding for item in response.data]
            else:
                logger.error("No embedding model available")
                return []
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return []
