"""
Enhanced AI Service that integrates Azure Document Intelligence and Qdrant Vector Database.
Replaces LlamaCloud with Azure + Qdrant solution.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import json
from datetime import datetime

import openai
from azure.identity.aio import DefaultAzureCredential

from ..models import (
    ExtractQuestionsRequest, ExtractQuestionsResponse,
    GenerateResponseRequest, GenerateResponseResponse,
    MultiStepResponse, Section, Question, QuestionCreate,
    StepType, StepStatus
)
from .azure_document_service import AzureDocumentService
from .qdrant_vector_service import QdrantVectorService

logger = logging.getLogger(__name__)

class EnhancedAIService:
    """
    Enhanced AI service using Azure Document Intelligence and Qdrant Vector Database.
    
    This service provides:
    - Document parsing and analysis with Azure Document Intelligence
    - Semantic search with Qdrant vector database
    - AI-powered question extraction and response generation
    - Multi-step response processing
    - Source tracking and attribution
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        azure_document_endpoint: Optional[str] = None,
        azure_storage_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None
    ):
        """
        Initialize Enhanced AI Service.
        
        Args:
            openai_api_key: OpenAI API key
            azure_document_endpoint: Azure Document Intelligence endpoint
            azure_storage_url: Azure Storage account URL
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key
        """
        self.openai_api_key = openai_api_key
        self.azure_document_endpoint = azure_document_endpoint
        self.azure_storage_url = azure_storage_url
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        
        # Initialize clients
        self.openai_client = None
        self.azure_credential = None
        self.document_service = None
        self.vector_service = None
        
        self._initialize_services()
    
    def configure(
        self,
        openai_api_key: Optional[str] = None,
        azure_document_endpoint: Optional[str] = None,
        azure_storage_url: Optional[str] = None,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None
    ):
        """Configure the AI service with new parameters."""
        if openai_api_key:
            self.openai_api_key = openai_api_key
        if azure_document_endpoint:
            self.azure_document_endpoint = azure_document_endpoint
        if azure_storage_url:
            self.azure_storage_url = azure_storage_url
        if qdrant_url:
            self.qdrant_url = qdrant_url
        if qdrant_api_key:
            self.qdrant_api_key = qdrant_api_key
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI and Azure services."""
        try:
            # Initialize OpenAI client
            if self.openai_api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=self.openai_api_key)
            
            # Initialize Azure credential
            self.azure_credential = DefaultAzureCredential()
            
            # Initialize Azure Document Service
            if self.azure_document_endpoint and self.azure_storage_url:
                self.document_service = AzureDocumentService(
                    document_intelligence_endpoint=self.azure_document_endpoint,
                    storage_account_url=self.azure_storage_url,
                    credential=self.azure_credential,
                    openai_client=self.openai_client
                )
            
            # Initialize Qdrant Vector Service
            if self.qdrant_url:
                self.vector_service = QdrantVectorService(
                    qdrant_url=self.qdrant_url,
                    qdrant_api_key=self.qdrant_api_key,
                    openai_client=self.openai_client
                )
            
            logger.info("AI services initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI services: {str(e)}")
    
    async def extract_questions(self, request: ExtractQuestionsRequest) -> ExtractQuestionsResponse:
        """
        Extract questions from document using Azure Document Intelligence.
        
        Args:
            request: Question extraction request
        
        Returns:
            Extracted questions organized by sections
        """
        try:
            if not self.document_service:
                raise ValueError("Azure Document Service not configured")
            
            # Mock file path - in real implementation, get from document record
            file_path = f"uploads/{request.project_id}/{request.document_id}.pdf"
            
            # Parse document with Azure Document Intelligence
            parsed_content = await self.document_service.parse_document(
                file_path=file_path,
                document_id=request.document_id,
                container_name=f"project-{request.project_id}"
            )
            
            # Extract questions using AI
            questions = await self.document_service.extract_questions_from_document(
                parsed_content=parsed_content,
                project_id=request.project_id
            )
            
            # Organize questions by sections
            sections = {}
            for question in questions:
                section_title = question.section_title or "General"
                if section_title not in sections:
                    sections[section_title] = Section(
                        title=section_title,
                        questions=[]
                    )
                
                # Convert QuestionCreate to Question (with generated ID)
                question_obj = Question(
                    id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set when saved
                    text=question.text,
                    section_title=question.section_title,
                    section_content=question.section_content,
                    page_number=question.page_number,
                    project_id=question.project_id,
                    metadata=question.metadata,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                sections[section_title].questions.append(question_obj)
            
            # Index document in vector database for future searches
            if self.vector_service:
                organization_id = UUID("00000000-0000-0000-0000-000000000000")  # Get from context
                await self.vector_service.index_document(
                    document=None,  # Document object would be passed here
                    parsed_content=parsed_content,
                    organization_id=organization_id
                )
            
            response = ExtractQuestionsResponse(
                success=True,
                sections=list(sections.values()),
                total_questions=len(questions),
                processing_time=0.0,  # Calculate actual time
                metadata={
                    "extraction_method": "azure_document_intelligence",
                    "document_pages": len(parsed_content.get("pages", [])),
                    "sections_found": len(sections),
                    "processed_at": datetime.now().isoformat()
                }
            )
            
            logger.info(f"Extracted {len(questions)} questions from document {request.document_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error extracting questions: {str(e)}")
            return ExtractQuestionsResponse(
                success=False,
                sections=[],
                total_questions=0,
                processing_time=0.0,
                error=str(e)
            )
    
    async def generate_response(self, request: GenerateResponseRequest) -> GenerateResponseResponse:
        """
        Generate AI response for a question using Qdrant vector search.
        
        Args:
            request: Response generation request
        
        Returns:
            Generated response with sources
        """
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not configured")
            
            if not self.vector_service:
                raise ValueError("Qdrant Vector Service not configured")
            
            # Get question context from vector database
            organization_id = UUID("00000000-0000-0000-0000-000000000000")  # Get from context
            project_id = UUID("00000000-0000-0000-0000-000000000000")  # Get from question
            
            context, sources = await self.vector_service.get_context_for_question(
                question=request.question_text,
                organization_id=organization_id,
                project_id=project_id
            )
            
            if not context:
                return GenerateResponseResponse(
                    success=False,
                    response="No relevant context found in documents.",
                    confidence=0.0,
                    sources=[],
                    metadata={"error": "No context available"}
                )
            
            # Generate response using OpenAI with context
            system_prompt = """
            You are an expert proposal writer responding to RFP (Request for Proposal) questions.
            
            Use the provided context from relevant documents to generate a comprehensive, accurate response.
            Your response should:
            1. Directly address the question asked
            2. Use specific information from the provided context
            3. Be professional and clear
            4. Include relevant details that demonstrate capability
            5. Reference specific sections or requirements when applicable
            
            If the context doesn't contain sufficient information to fully answer the question, 
            indicate what additional information would be needed.
            """
            
            user_prompt = f"""
            Question: {request.question_text}
            
            Relevant Context from Documents:
            {context}
            
            Please provide a comprehensive response to this question based on the provided context.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # Calculate confidence based on context relevance
            confidence = min(0.95, len(sources) * 0.15 + 0.5)
            
            # Format sources
            formatted_sources = []
            for source in sources[:5]:  # Limit to top 5 sources
                formatted_sources.append({
                    "document_id": source["document_id"],
                    "document_name": source["document_name"],
                    "page_number": source["page_number"],
                    "relevance_score": source["relevance_score"],
                    "text_excerpt": source["text_excerpt"]
                })
            
            return GenerateResponseResponse(
                success=True,
                response=ai_response,
                confidence=confidence,
                sources=formatted_sources,
                metadata={
                    "generation_method": "azure_qdrant_enhanced",
                    "context_length": len(context),
                    "sources_used": len(sources),
                    "model_used": "gpt-4",
                    "generated_at": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return GenerateResponseResponse(
                success=False,
                response="An error occurred while generating the response.",
                confidence=0.0,
                sources=[],
                metadata={"error": str(e)}
            )
    
    async def multi_step_generate_response(self, request: GenerateResponseRequest) -> MultiStepResponse:
        """
        Generate response using multi-step analysis process.
        
        Args:
            request: Response generation request
        
        Returns:
            Multi-step response with detailed processing steps
        """
        try:
            steps = []
            start_time = datetime.now()
            
            # Step 1: Analyze Question
            steps.append({
                "step_type": StepType.ANALYZE_QUESTION,
                "status": StepStatus.RUNNING,
                "description": "Analyzing question complexity and requirements",
                "started_at": datetime.now().isoformat()
            })
            
            question_analysis = await self._analyze_question_complexity(request.question_text)
            steps[-1].update({
                "status": StepStatus.COMPLETED,
                "result": question_analysis,
                "completed_at": datetime.now().isoformat()
            })
            
            # Step 2: Search Documents
            steps.append({
                "step_type": StepType.SEARCH_DOCUMENTS,
                "status": StepStatus.RUNNING,
                "description": "Searching relevant documents using semantic search",
                "started_at": datetime.now().isoformat()
            })
            
            if self.vector_service:
                organization_id = UUID("00000000-0000-0000-0000-000000000000")  # Get from context
                project_id = UUID("00000000-0000-0000-0000-000000000000")  # Get from question
                
                search_results = await self.vector_service.search_similar_content(
                    query=request.question_text,
                    organization_id=organization_id,
                    project_id=project_id,
                    limit=15
                )
                
                steps[-1].update({
                    "status": StepStatus.COMPLETED,
                    "result": {"documents_found": len(search_results)},
                    "completed_at": datetime.now().isoformat()
                })
            else:
                steps[-1].update({
                    "status": StepStatus.FAILED,
                    "result": {"error": "Vector service not available"},
                    "completed_at": datetime.now().isoformat()
                })
                search_results = []
            
            # Step 3: Extract Information
            steps.append({
                "step_type": StepType.EXTRACT_INFORMATION,
                "status": StepStatus.RUNNING,
                "description": "Extracting relevant information from found documents",
                "started_at": datetime.now().isoformat()
            })
            
            context, sources = await self._extract_relevant_information(
                search_results, request.question_text
            )
            
            steps[-1].update({
                "status": StepStatus.COMPLETED,
                "result": {"context_length": len(context), "sources_count": len(sources)},
                "completed_at": datetime.now().isoformat()
            })
            
            # Step 4: Synthesize Response
            steps.append({
                "step_type": StepType.SYNTHESIZE_RESPONSE,
                "status": StepStatus.RUNNING,
                "description": "Generating comprehensive response using AI",
                "started_at": datetime.now().isoformat()
            })
            
            if self.openai_client and context:
                response = await self._synthesize_response(
                    request.question_text, context, question_analysis
                )
                steps[-1].update({
                    "status": StepStatus.COMPLETED,
                    "result": {"response_length": len(response)},
                    "completed_at": datetime.now().isoformat()
                })
            else:
                response = "Unable to generate response due to missing context or AI service."
                steps[-1].update({
                    "status": StepStatus.FAILED,
                    "result": {"error": "Missing context or AI service"},
                    "completed_at": datetime.now().isoformat()
                })
            
            # Step 5: Validate Answer
            steps.append({
                "step_type": StepType.VALIDATE_ANSWER,
                "status": StepStatus.RUNNING,
                "description": "Validating response quality and completeness",
                "started_at": datetime.now().isoformat()
            })
            
            validation_result = await self._validate_response(request.question_text, response, sources)
            steps[-1].update({
                "status": StepStatus.COMPLETED,
                "result": validation_result,
                "completed_at": datetime.now().isoformat()
            })
            
            # Calculate overall metrics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return MultiStepResponse(
                steps=steps,
                final_response=response,
                sources=sources[:5],  # Top 5 sources
                overall_confidence=validation_result.get("confidence", 0.7),
                processing_time=processing_time,
                metadata={
                    "method": "azure_qdrant_multi_step",
                    "question_complexity": question_analysis.get("complexity", "moderate"),
                    "total_steps": len(steps),
                    "completed_at": end_time.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error in multi-step response generation: {str(e)}")
            return MultiStepResponse(
                steps=[],
                final_response="An error occurred during multi-step processing.",
                sources=[],
                overall_confidence=0.0,
                processing_time=0.0,
                metadata={"error": str(e)}
            )
    
    async def _analyze_question_complexity(self, question: str) -> Dict[str, Any]:
        """Analyze question complexity and requirements."""
        if not self.openai_client:
            return {"complexity": "moderate", "analysis": "AI analysis not available"}
        
        try:
            system_prompt = """
            Analyze the complexity and requirements of this RFP question.
            Determine:
            1. Complexity level (simple, moderate, complex, multi-part)
            2. Key topics and themes
            3. Type of response needed (technical, commercial, process, etc.)
            4. Estimated response length needed
            
            Return JSON format:
            {
                "complexity": "simple|moderate|complex|multi-part",
                "topics": ["topic1", "topic2"],
                "response_type": "technical|commercial|process|administrative",
                "estimated_length": "short|medium|long",
                "key_requirements": ["req1", "req2"]
            }
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question}"}
                ],
                temperature=0.1
            )
            
            try:
                analysis = json.loads(response.choices[0].message.content)
                return analysis
            except json.JSONDecodeError:
                return {"complexity": "moderate", "analysis": "Failed to parse analysis"}
                
        except Exception as e:
            logger.error(f"Error analyzing question complexity: {str(e)}")
            return {"complexity": "moderate", "error": str(e)}
    
    async def _extract_relevant_information(
        self,
        search_results: List[Dict[str, Any]],
        question: str
    ) -> tuple[str, List[Dict[str, Any]]]:
        """Extract and combine relevant information from search results."""
        if not search_results:
            return "", []
        
        # Combine top results into context
        context_parts = []
        sources = []
        max_context_length = 4000
        current_length = 0
        
        for result in search_results:
            text = result["text"]
            if current_length + len(text) > max_context_length:
                break
            
            context_parts.append(f"[{result['document_name']}, Page {result['page_number']}]\n{text}")
            current_length += len(text)
            
            sources.append({
                "document_id": result["document_id"],
                "document_name": result["document_name"],
                "page_number": result["page_number"],
                "relevance_score": result["score"],
                "text_excerpt": text[:200] + "..." if len(text) > 200 else text
            })
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    async def _synthesize_response(
        self,
        question: str,
        context: str,
        question_analysis: Dict[str, Any]
    ) -> str:
        """Synthesize final response using AI."""
        if not self.openai_client:
            return "AI response generation not available."
        
        try:
            complexity = question_analysis.get("complexity", "moderate")
            response_type = question_analysis.get("response_type", "general")
            
            system_prompt = f"""
            You are an expert proposal writer responding to RFP questions.
            
            Question complexity: {complexity}
            Response type: {response_type}
            
            Generate a comprehensive, professional response that:
            1. Directly addresses all aspects of the question
            2. Uses specific information from the provided context
            3. Demonstrates capability and expertise
            4. Is appropriately detailed for the complexity level
            5. Includes relevant examples or specifics when available
            
            Keep the response focused and well-structured.
            """
            
            user_prompt = f"""
            Question: {question}
            
            Relevant Context:
            {context}
            
            Please provide a comprehensive response.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return "An error occurred while generating the response."
    
    async def _validate_response(
        self,
        question: str,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate response quality and completeness."""
        try:
            # Basic validation metrics
            validation = {
                "confidence": 0.7,
                "completeness": "partial",
                "source_coverage": len(sources),
                "response_length": len(response),
                "validation_notes": []
            }
            
            # Check response length appropriateness
            if len(response) < 100:
                validation["validation_notes"].append("Response may be too brief")
                validation["confidence"] -= 0.1
            elif len(response) > 2000:
                validation["validation_notes"].append("Response may be too lengthy")
            
            # Check source coverage
            if len(sources) == 0:
                validation["confidence"] = 0.3
                validation["completeness"] = "poor"
                validation["validation_notes"].append("No sources available")
            elif len(sources) < 3:
                validation["confidence"] -= 0.1
                validation["validation_notes"].append("Limited source coverage")
            else:
                validation["completeness"] = "good"
            
            # Ensure confidence bounds
            validation["confidence"] = max(0.1, min(0.95, validation["confidence"]))
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}")
            return {
                "confidence": 0.5,
                "completeness": "unknown",
                "source_coverage": 0,
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.document_service:
            await self.document_service.cleanup()
        if self.openai_client:
            await self.openai_client.close()

# Global service instance
enhanced_ai_service = EnhancedAIService()
