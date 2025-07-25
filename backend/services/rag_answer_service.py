"""
RAG-based Answer Generation Service for RFP Questions
Uses Qdrant Vector Store with Azure OpenAI for intelligent response generation
"""

import os
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

# Azure OpenAI
from openai import AsyncAzureOpenAI

# Qdrant Vector Database
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, MatchAny, SearchRequest,
    VectorParams, Distance
)

# LangChain integration for embeddings and sparse search
from langchain_openai import AzureOpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore, RetrievalMode, FastEmbedSparse

from models import GenerateResponseRequest, GenerateResponseResponse, Question, Answer, Source
from database_config import database, get_table_name

logger = logging.getLogger(__name__)

class RAGAnswerService:
    """
    RAG-based Answer Generation Service for RFP Questions.
    
    Features:
    - Semantic search in RFP_AI_Collection
    - Context-aware answer generation
    - Source attribution and confidence scoring
    - Multi-step reasoning for complex questions
    """
    
    def __init__(self):
        """Initialize RAG Answer Service with Azure OpenAI and Qdrant."""
        
        # Azure OpenAI Configuration
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_api_version = os.getenv("AZURE_API_VERSION", "2024-10-21")
        self.deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4.1-mini")
        
        # Qdrant Configuration
        self.qdrant_url = os.getenv("QDRANT_URL") or os.getenv("QDRANT_PROD_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY") or os.getenv("QDRANT_PROD_API_KEY")
        self.collection_name = "RFP_AI_Collection"
        
        # Initialize clients
        self._initialize_clients()
        
        # Search configuration
        self.max_context_chunks = 8
        self.min_similarity_score = 0.6
        self.max_context_length = 6000
        
    def _initialize_clients(self):
        """Initialize Azure OpenAI and Qdrant clients."""
        try:
            # Azure OpenAI Client
            if self.azure_endpoint and self.azure_api_key:
                self.openai_client = AsyncAzureOpenAI(
                    azure_endpoint=self.azure_endpoint,
                    api_key=self.azure_api_key,
                    api_version=self.azure_api_version
                )
                print("[OK] Azure OpenAI client initialized")
            else:
                self.openai_client = None
                print("[WARN] Azure OpenAI not configured - using mock responses")
            
            # Qdrant Client
            if self.qdrant_url and self.qdrant_api_key:
                self.qdrant_client = QdrantClient(
                    url=self.qdrant_url,
                    api_key=self.qdrant_api_key
                )
                print(f"[OK] Qdrant client initialized for collection: {self.collection_name}")
                
                # Initialize embeddings for vector search (matching vivavis.py)
                self.embeddings = AzureOpenAIEmbeddings(
                    model="text-embedding-3-large-2"
                ) if self.azure_endpoint else None
                
                # Initialize sparse embeddings for hybrid search (matching vivavis.py)
                self.sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
                
            else:
                self.qdrant_client = None
                self.embeddings = None
                self.sparse_embeddings = None
                print("[WARN] Qdrant not configured - using mock responses")
                
        except Exception as e:
            print(f"[ERROR] Error initializing RAG clients: {e}")
            self.openai_client = None
            self.qdrant_client = None
            self.embeddings = None
            self.sparse_embeddings = None
    
    async def generate_answer(self, request: GenerateResponseRequest) -> GenerateResponseResponse:
        """
        Generate an AI-powered answer to an RFP question using RAG.
        
        Args:
            request: Contains question, project_id, and search parameters
            
        Returns:
            Generated response with sources and metadata
        """
        try:
            print(f"[RAG] Generating answer for question: {request.question[:100]}...")
            
            # Step 1: Analyze question and determine smart filters
            organization_id = getattr(request, 'organization_id', None)
            smart_filters = await self._analyze_question_for_smart_filtering(request.question)
            
            # Step 2: Retrieve relevant context from vector store
            context_chunks, sources = await self._retrieve_context(
                query=request.question,
                project_id=getattr(request, 'project_id', None),
                organization_id=organization_id,
                document_filters=smart_filters,
                top_k=self.max_context_chunks
            )
            
            # Step 3: Generate answer using context
            if self.openai_client and context_chunks:
                answer_text, confidence = await self._generate_contextual_answer(
                    question=request.question,
                    context_chunks=context_chunks
                )
            else:
                # Fallback to mock response
                answer_text, confidence = await self._generate_mock_answer(request.question)
                sources = []
            
            # Step 4: Save answer to database
            answer = await self._save_answer(
                question_id=getattr(request, 'question_id', None),
                answer_text=answer_text,
                confidence=confidence,
                sources=sources
            )
            
            # Step 5: Create response
            response = GenerateResponseResponse(
                success=True,
                response=answer_text,
                sources=sources,
                metadata={
                    "confidence": confidence,
                    "context_chunks_used": len(context_chunks),
                    "search_method": "qdrant_rag" if self.qdrant_client else "mock",
                    "generated_at": datetime.now().isoformat(),
                    "model_used": self.deployment_name,
                    "collection": self.collection_name
                }
            )
            
            print(f"[SUCCESS] Answer generated with {len(sources)} sources, confidence: {confidence:.2f}")
            return response
            
        except Exception as e:
            print(f"[ERROR] Error generating answer: {e}")
            # Return error response
            return GenerateResponseResponse(
                success=False,
                response=f"I apologize, but I encountered an error while generating a response to your question. Please try again later.",
                sources=[],
                metadata={
                    "error": str(e),
                    "generated_at": datetime.now().isoformat(),
                    "confidence": 0.0
                }
            )
    
    async def _retrieve_context(
        self, 
        query: str, 
        project_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        document_filters: Optional[Dict[str, Any]] = None,
        top_k: int = 8
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Retrieve relevant context chunks from Qdrant vector store with intelligent filtering.
        
        Args:
            query: The question to search for
            project_id: Optional project filter
            organization_id: Optional organization filter
            document_filters: Optional filters for document types, tags, etc.
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (context_chunks, sources)
        """
        if not self.qdrant_client or not self.embeddings:
            print("[WARN] Qdrant not available, returning empty context")
            return [], []
        
        try:
            print(f"[SEARCH] Searching RFP_AI_Collection for: {query[:100]}...")
            
            # DIRECT QDRANT SEARCH (bypassing LangChain for debugging)
            print(f"[DEBUG] Creating query vector...")
            query_vector = self.embeddings.embed_query(query)
            print(f"[DEBUG] Query vector created: {len(query_vector)} dimensions")
            
            print(f"[DEBUG] Performing direct Qdrant search...")
            direct_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            
            print(f"[DEBUG] Direct search found {len(direct_results)} results")
            
            # Convert direct results to our format and use them instead of LangChain
            context_chunks = []
            sources = []
            
            for i, result in enumerate(direct_results):
                print(f"[DEBUG] Processing result {i+1}:")
                print(f"  Score: {result.score}")
                print(f"  ID: {result.id}")
                print(f"  Payload keys: {list(result.payload.keys())}")
                
                content = result.payload.get('content', '')
                print(f"  Content length: {len(content)}")
                print(f"  Content preview: {content[:200]}...")
                
                if content:  # Only add if content exists
                    chunk_data = {
                        "content": content,
                        "score": float(result.score),
                        "metadata": {
                            "filename": result.payload.get("filename", "Unknown"),
                            "document_type": result.payload.get("document_type", "Unknown"),
                            "industry_tags": result.payload.get("industry_tags", []),
                            "capability_tags": result.payload.get("capability_tags", []),
                            "organization_id": result.payload.get("organization_id", ""),
                            "document_id": result.payload.get("document_id", result.id)
                        }
                    }
                    context_chunks.append(chunk_data)
                    
                    # Create source info
                    source = {
                        "id": len(sources) + 1,
                        "fileName": result.payload.get("filename", "Unknown"),
                        "pageNumber": "1",
                        "relevance": int(result.score * 100),
                        "textContent": content[:200] + "..." if len(content) > 200 else content
                    }
                    sources.append(source)
            
            print(f"[SUCCESS] Using direct Qdrant results: {len(context_chunks)} chunks with content")
            return context_chunks, sources
            
        except Exception as e:
            print(f"[ERROR] Error retrieving context: {e}")
            return [], []
    
    async def _generate_contextual_answer(
        self, 
        question: str, 
        context_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, float]:
        """
        Generate an answer using Azure OpenAI with retrieved context.
        
        Args:
            question: The RFP question to answer
            context_chunks: Retrieved context from vector store
            
        Returns:
            Tuple of (answer_text, confidence_score)
        """
        try:
            # Prepare context
            context_text = self._prepare_context(context_chunks)
            
            # Create system prompt for RFP response generation
            system_prompt = """You are an expert RFP response writer helping create professional, comprehensive answers to Request for Proposal questions.

Your task is to:
1. Analyze the provided context from company documents and knowledge base
2. Generate a professional, detailed response that directly addresses the question
3. Use specific information from the context when available
4. Maintain a professional, confident tone appropriate for business proposals
5. Structure your response clearly with bullet points or paragraphs as appropriate
6. If the context doesn't contain sufficient information, acknowledge this and provide general best practices

Guidelines:
- Be specific and detailed in your responses
- Use quantifiable metrics when available in the context
- Reference relevant experience and capabilities from the context
- Maintain consistency with company messaging and positioning
- Focus on value proposition and differentiators
- End with a clear commitment or next step when appropriate"""

            user_prompt = f"""Please provide a comprehensive answer to this RFP question based on the retrieved context:

**Question:** {question}

**Hier sind die relevanten Chunks aus der Datenbank:**
{context_text}

Please provide a professional, detailed response that demonstrates our capabilities and addresses all aspects of the question. Use the specific information from the chunks above."""

            # DEBUG: Print the complete prompt and context
            print("\n" + "="*80)
            print("🔍 RAG DEBUG INFO")
            print("="*80)
            print(f"📋 SYSTEM PROMPT:")
            print(f"{system_prompt}")
            print(f"\n📝 USER PROMPT:")
            print(f"{user_prompt}")
            print(f"\n📊 CONTEXT CHUNKS COUNT: {len(context_chunks)}")
            for i, chunk in enumerate(context_chunks, 1):
                print(f"\n--- CHUNK {i} DEBUG ---")
                print(f"Score: {chunk.get('score', 'N/A')}")
                print(f"Metadata: {chunk.get('metadata', {})}")
                print(f"Content Length: {len(chunk.get('content', ''))}")
                print(f"Content Preview: {chunk.get('content', '')[:200]}...")
            print("="*80)

            # Generate response
            response = await self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent responses
                max_tokens=1500
            )
            
            answer_text = response.choices[0].message.content.strip()
            
            # Calculate confidence based on context quality and response length
            confidence = self._calculate_confidence(context_chunks, answer_text)
            
            # DEBUG: Print the generated answer
            print(f"\n🤖 GENERATED ANSWER:")
            print(f"{answer_text}")
            print(f"\n📈 CONFIDENCE: {confidence:.2f}")
            print("="*80 + "\n")
            
            print(f"[SUCCESS] Generated contextual answer ({len(answer_text)} chars, confidence: {confidence:.2f})")
            return answer_text, confidence
            
        except Exception as e:
            print(f"[ERROR] Error generating contextual answer: {e}")
            return await self._generate_mock_answer(question)
    
    def _prepare_context(self, context_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context text from retrieved chunks with clear chunk separation."""
        if not context_chunks:
            return "Keine relevanten Dokumente gefunden."
        
        context_parts = []
        total_length = 0
        
        for i, chunk in enumerate(context_chunks, 1):
            content = chunk["content"]
            metadata = chunk.get("metadata", {})
            score = chunk.get("score", 0)
            
            # Clear chunk header
            context_parts.append(f"=== CHUNK {i} ===")
            context_parts.append(f"Relevanz-Score: {score:.3f}")
            context_parts.append(f"Quelle: {metadata.get('filename', 'Unknown')}")
            context_parts.append(f"Dokumenttyp: {metadata.get('document_type', 'Unknown')}")
            
            # Add metadata if available
            industry_tags = metadata.get('industry_tags', [])
            capability_tags = metadata.get('capability_tags', [])
            if industry_tags:
                industry_str = ', '.join(industry_tags) if isinstance(industry_tags, list) else str(industry_tags)
                context_parts.append(f"Branchen: {industry_str}")
            if capability_tags:
                capability_str = ', '.join(capability_tags) if isinstance(capability_tags, list) else str(capability_tags)
                context_parts.append(f"Fähigkeiten: {capability_str}")
            
            context_parts.append(f"Inhalt:")
            context_parts.append(f"{content}")
            context_parts.append("")  # Empty line between chunks
            
            # Check length limits
            current_chunk = "\n".join(context_parts[-8:])  # Last 8 lines for this chunk
            if total_length + len(current_chunk) > self.max_context_length:
                break
                
            total_length += len(current_chunk)
        
        return "\n".join(context_parts)
    
    def _calculate_confidence(self, context_chunks: List[Dict[str, Any]], answer_text: str) -> float:
        """Calculate confidence score based on context quality and answer."""
        if not context_chunks:
            return 0.3  # Low confidence without context
        
        # Base confidence from search scores
        avg_score = sum(chunk.get("score", 0) for chunk in context_chunks) / len(context_chunks)
        
        # Adjust for answer length and quality indicators
        length_factor = min(len(answer_text) / 1500, 1.0)  # Normalize to 0-1 based on max_tokens
        chunk_factor = min(len(context_chunks) / 5, 1.0)  # More chunks = higher confidence
        
        confidence = (avg_score * 0.6 + length_factor * 0.2 + chunk_factor * 0.2)
        return min(max(confidence, 0.1), 0.95)  # Clamp between 0.1 and 0.95
    
    async def _generate_mock_answer(self, question: str) -> Tuple[str, float]:
        """Generate a mock answer when AI services are not available."""
        mock_answers = {
            "experience": "Our company has extensive experience in similar projects, with over 15 years of proven track record in delivering high-quality solutions. We have successfully completed projects across various industries and have built strong relationships with clients who continue to work with us on multiple engagements.",
            
            "approach": "Our proposed approach focuses on a collaborative, agile methodology that ensures transparency and continuous communication throughout the project lifecycle. We begin with comprehensive requirements gathering, followed by iterative development cycles that allow for regular feedback and adjustments.",
            
            "timeline": "Based on our analysis of the project requirements, we propose a timeline of 12-16 weeks for complete delivery. This includes initial planning and setup (2 weeks), development phases (8-10 weeks), testing and quality assurance (2 weeks), and deployment and training (2 weeks).",
            
            "team": "Our dedicated team consists of senior professionals with specialized expertise in the relevant technologies and industry domain. Each team member brings unique skills and experience, ensuring comprehensive coverage of all project requirements.",
            
            "cost": "Our pricing structure is competitive and transparent, providing excellent value for the level of expertise and quality delivered. We offer flexible engagement models including fixed-price, time-and-materials, and hybrid approaches to best suit your project needs."
        }
        
        # Simple keyword matching for mock responses
        question_lower = question.lower()
        for key, answer in mock_answers.items():
            if key in question_lower:
                return f"**{answer}**\n\n*Please note: This is a template response. For a detailed, project-specific answer, please ensure your knowledge base is populated with relevant company information.*", 0.4
        
        return f"Thank you for your question. We would be happy to provide detailed information addressing your specific requirements. Our team will review your question and provide a comprehensive response that demonstrates our capabilities and approach.\n\n*Please note: This is a template response. For detailed answers, please ensure your knowledge base is populated with relevant company information.*", 0.3
    
    async def _save_answer(
        self,
        question_id: Optional[str],
        answer_text: str,
        confidence: float,
        sources: List[Dict[str, Any]]
    ) -> Optional[Answer]:
        """Save the generated answer to the database."""
        if not question_id:
            return None
            
        try:
            answers_table = get_table_name("answers")
            
            # Create answer record
            answer_id = str(uuid.uuid4())
            
            query = f"""
                INSERT INTO {answers_table} 
                (id, question_id, text, confidence, created_at, updated_at)
                VALUES (:id, :question_id, :text, :confidence, :created_at, :updated_at)
            """
            
            await database.execute(query, {
                "id": answer_id,
                "question_id": question_id,
                "text": answer_text,
                "confidence": confidence,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            # Note: Sources are returned in the response metadata but not stored in database
            # In a production system, you might want to store sources in a separate table
            
            print(f"[SUCCESS] Answer saved to database: {answer_id}")
            return {"id": answer_id, "text": answer_text, "confidence": confidence}
            
        except Exception as e:
            print(f"[ERROR] Error saving answer: {e}")
            return None
    
    async def search_knowledge_base(
        self, 
        query: str, 
        top_k: int = 5,
        project_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for relevant information.
        Useful for testing and debugging the RAG system.
        """
        context_chunks, sources = await self._retrieve_context(
            query=query,
            project_id=project_filter,
            top_k=top_k
        )
        
        return {
            "query": query,
            "results_count": len(context_chunks),
            "chunks": context_chunks,
            "sources": sources
        }
    
    async def _analyze_question_for_smart_filtering(self, question: str) -> Dict[str, Any]:
        """
        Analyze RFP question to determine relevant document filters.
        Uses keyword matching and AI analysis to select appropriate document types and tags.
        """
        question_lower = question.lower()
        filters = {}
        
        # Document type analysis
        if any(word in question_lower for word in ["experience", "past", "previous", "track record", "portfolio"]):
            filters["document_types"] = ["case_study", "company_profile"]
        
        elif any(word in question_lower for word in ["team", "staff", "personnel", "resources", "qualifications"]):
            filters["document_types"] = ["team_bios", "company_profile"]
        
        elif any(word in question_lower for word in ["technical", "technology", "architecture", "specs", "specifications"]):
            filters["document_types"] = ["technical_specs", "methodology"]
        
        elif any(word in question_lower for word in ["cost", "price", "budget", "pricing", "rate"]):
            filters["document_types"] = ["pricing_templates", "case_study"]
        
        elif any(word in question_lower for word in ["approach", "methodology", "process", "framework"]):
            filters["document_types"] = ["methodology", "case_study"]
        
        elif any(word in question_lower for word in ["certification", "compliance", "standard", "iso", "sox", "hipaa"]):
            filters["document_types"] = ["certifications", "company_profile"]
        
        # Industry analysis
        if any(word in question_lower for word in ["healthcare", "medical", "hospital", "patient"]):
            filters["industry_tags"] = ["healthcare"]
        
        elif any(word in question_lower for word in ["financial", "banking", "fintech", "payment"]):
            filters["industry_tags"] = ["finance"]
        
        elif any(word in question_lower for word in ["government", "federal", "state", "public sector"]):
            filters["industry_tags"] = ["government"]
        
        elif any(word in question_lower for word in ["manufacturing", "production", "supply chain"]):
            filters["industry_tags"] = ["manufacturing"]
        
        # Capability analysis
        if any(word in question_lower for word in ["cloud", "aws", "azure", "migration"]):
            filters["capability_tags"] = ["cloud_migration"]
        
        elif any(word in question_lower for word in ["data", "analytics", "reporting", "dashboard"]):
            filters["capability_tags"] = ["data_analytics"]
        
        elif any(word in question_lower for word in ["security", "cybersecurity", "encryption", "vulnerability"]):
            filters["capability_tags"] = ["cybersecurity"]
        
        elif any(word in question_lower for word in ["ai", "machine learning", "ml", "artificial intelligence"]):
            filters["capability_tags"] = ["ai_ml"]
        
        elif any(word in question_lower for word in ["integration", "api", "connect", "interface"]):
            filters["capability_tags"] = ["integration"]
        
        elif any(word in question_lower for word in ["mobile", "app", "ios", "android"]):
            filters["capability_tags"] = ["mobile_development"]
        
        # Confidence level preference for complex questions
        complexity_indicators = ["complex", "enterprise", "large-scale", "mission-critical", "strategic"]
        if any(indicator in question_lower for indicator in complexity_indicators):
            filters["confidence_level"] = "high"
        
        return filters
    
    async def generate_answer_with_filters(
        self, 
        question: str, 
        organization_id: str,
        explicit_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate answer with explicit document filters (for API endpoint).
        """
        try:
            # Combine smart filters with explicit filters
            smart_filters = await self._analyze_question_for_smart_filtering(question)
            final_filters = {**smart_filters, **(explicit_filters or {})}
            
            # Retrieve context with filters
            context_chunks, sources = await self._retrieve_context(
                query=question,
                organization_id=organization_id,
                document_filters=final_filters,
                top_k=self.max_context_chunks
            )
            
            # Generate answer
            if self.openai_client and context_chunks:
                answer_text, confidence = await self._generate_contextual_answer(
                    question=question,
                    context_chunks=context_chunks
                )
            else:
                answer_text, confidence = await self._generate_mock_answer(question)
                sources = []
            
            return {
                "success": True,
                "answer": answer_text,
                "confidence": confidence,
                "sources": sources,
                "filters_applied": final_filters,
                "context_chunks_used": len(context_chunks),
                "organization_id": organization_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filters_applied": explicit_filters or {},
                "organization_id": organization_id
            }

# Global service instance
rag_answer_service = RAGAnswerService()