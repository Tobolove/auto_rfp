"""
RAG-based response generation service for RFP questions.
Combines question context with company knowledge via vector search to generate AI responses.
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import AsyncAzureOpenAI
from models import (
    GenerateResponseRequest, GenerateResponseResponse, 
    Answer, Source, SourceData
)
from database_config import database, get_table_name
from services.qdrant_service import qdrant_service
from services.question_extraction_service import question_extraction_service


class ResponseGenerationService:
    """Service for generating AI-powered responses to RFP questions using RAG."""
    
    def __init__(self):
        # Azure OpenAI setup
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = "gpt-4"  # Adjust based on your deployment
        
        if self.azure_endpoint and self.azure_key:
            self.client = AsyncAzureOpenAI(
                azure_endpoint=self.azure_endpoint,
                api_key=self.azure_key,
                api_version="2024-02-15-preview"
            )
        else:
            self.client = None
            print("Warning: Azure OpenAI not configured, using mock responses")
    
    async def generate_response_for_question(self, request: GenerateResponseRequest) -> GenerateResponseResponse:
        """Generate a comprehensive response to an RFP question using RAG."""
        try:
            # Get the question details
            question = await self._get_question(str(request.question_id))
            if not question:
                raise ValueError(f"Question {request.question_id} not found")
            
            # Get organization for vector search
            project = await self._get_project(str(question.project_id))
            if not project:
                raise ValueError("Project not found")
            
            # Search for relevant company knowledge
            relevant_content = await qdrant_service.search_relevant_content(
                organization_id=str(project.organization_id),
                query=question.text,
                limit=5,
                score_threshold=0.6
            )
            
            # Generate response using AI + RAG
            if self.client and relevant_content:
                response_text, confidence = await self._generate_with_azure_openai(
                    question, relevant_content, request.additional_context
                )
            else:
                response_text, confidence = await self._generate_mock_response(
                    question, relevant_content
                )
            
            # Create answer record
            answer = Answer(
                id=uuid.uuid4(),
                question_id=question.id,
                text=response_text,
                confidence=confidence,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Save answer to database
            await self._save_answer(answer)
            
            # Create sources from relevant content
            sources = []
            for i, content in enumerate(relevant_content[:3]):  # Limit to top 3 sources
                source = Source(
                    id=uuid.uuid4(),
                    answer_id=answer.id,
                    file_name=content.get("document_name", f"Source {i+1}"),
                    file_path=content.get("file_path"),
                    page_number=str(content.get("chunk_index", "")),
                    document_id=content.get("document_id"),
                    relevance=int(content.get("score", 0.5) * 100),
                    text_content=content.get("text", "")[:500],  # Limit text length
                    created_at=datetime.now()
                )
                sources.append(source)
                
                # Save source to database
                await self._save_source(source)
            
            return GenerateResponseResponse(
                question_id=request.question_id,
                answer_id=answer.id,
                text=response_text,
                confidence=confidence,
                sources=sources,
                generation_method="rag_azure_openai" if self.client else "mock_rag",
                context_used=len(relevant_content),
                processing_time=3.2  # Placeholder
            )
            
        except Exception as e:
            print(f"Response generation failed: {e}")
            raise
    
    async def _generate_with_azure_openai(
        self, 
        question: Any, 
        relevant_content: List[Dict[str, Any]], 
        additional_context: Optional[str] = None
    ) -> tuple[str, float]:
        """Generate response using Azure OpenAI with RAG context."""
        
        # Prepare context from relevant content
        context_sections = []
        for i, content in enumerate(relevant_content):
            context_sections.append(f"""
Source {i+1} (from {content.get('document_name', 'Unknown Document')}):
{content.get('text', '')}
""")
        
        context_text = "\n".join(context_sections)
        
        system_prompt = """You are an expert RFP response writer helping a company respond to Request for Proposal questions. 

Your task is to:
1. Analyze the RFP question carefully
2. Use the provided company knowledge and context to craft a comprehensive response
3. Ensure the response directly addresses what is being asked
4. Be specific and provide concrete examples when possible
5. Maintain a professional, confident tone
6. If the provided context doesn't fully answer the question, be honest about limitations

Guidelines:
- Start with a direct answer to the question
- Support your answer with specific details from the company knowledge
- Use quantifiable metrics when available
- Address all parts of multi-part questions
- Keep responses focused and relevant
- Cite specific sources when referencing company capabilities

The response should be suitable for inclusion in a formal RFP submission."""

        user_prompt = f"""
RFP Question: {question.text}

Question Topic: {question.topic}
Section: {question.section_title}

Company Knowledge Context:
{context_text}

Additional Context: {additional_context or "None provided"}

Please provide a comprehensive response to this RFP question using the company knowledge provided above.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent responses
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content
            
            # Calculate confidence based on context quality and response length
            context_score = min(len(relevant_content) * 0.2, 0.8)  # More context = higher confidence
            response_length_score = min(len(response_text) / 1000, 0.2)  # Longer responses get slight boost
            confidence = context_score + response_length_score
            
            return response_text, min(confidence, 0.95)  # Cap at 95%
            
        except Exception as e:
            print(f"Azure OpenAI generation failed: {e}")
            # Fallback to context-based response
            return await self._generate_context_based_response(question, relevant_content)
    
    async def _generate_context_based_response(
        self, 
        question: Any, 
        relevant_content: List[Dict[str, Any]]
    ) -> tuple[str, float]:
        """Generate a simple response based on available context."""
        if not relevant_content:
            return (
                f"Thank you for your question regarding {question.topic.lower()}. "
                f"Our team has extensive experience in this area and would be happy to "
                f"discuss our capabilities and approach in detail during the proposal process.",
                0.4
            )
        
        # Create a basic response using the most relevant content
        top_content = relevant_content[0]
        response = f"""Based on our company knowledge and experience:

{top_content.get('text', '')[:500]}

Our organization is well-positioned to address the requirements outlined in your RFP. We would welcome the opportunity to provide additional details and discuss how our capabilities align with your specific needs.

For more detailed information, please refer to our {top_content.get('document_name', 'company documentation')}."""
        
        confidence = min(0.7, len(relevant_content) * 0.15)
        return response, confidence
    
    async def _generate_mock_response(
        self, 
        question: Any, 
        relevant_content: List[Dict[str, Any]]
    ) -> tuple[str, float]:
        """Generate a mock response for development/testing."""
        
        topic_responses = {
            "experience": f"Our organization has extensive experience in {question.topic.lower()}. We have successfully completed numerous similar projects and have a proven track record of delivering high-quality results.",
            
            "technical": f"From a technical perspective, our approach to {question.topic.lower()} involves industry best practices and cutting-edge methodologies. We leverage advanced tools and techniques to ensure optimal outcomes.",
            
            "project management": f"Our project management approach for {question.topic.lower()} follows established frameworks and includes comprehensive planning, risk management, and quality assurance processes.",
            
            "team": f"Our team includes highly qualified professionals with specialized expertise in {question.topic.lower()}. All team members hold relevant certifications and have extensive hands-on experience.",
            
            "cost": f"Our pricing for {question.topic.lower()} is competitive and provides excellent value. We offer transparent pricing with detailed breakdowns and flexible engagement models."
        }
        
        # Find the most appropriate response template
        topic_lower = question.topic.lower()
        response_template = topic_responses.get("technical")  # Default
        
        for key, template in topic_responses.items():
            if key in topic_lower:
                response_template = template
                break
        
        # Add context if available
        if relevant_content:
            context_snippet = relevant_content[0].get('text', '')[:200]
            response = f"{response_template}\n\nBased on our documented capabilities: {context_snippet}..."
            confidence = 0.7
        else:
            response = response_template
            confidence = 0.5
        
        return response, confidence
    
    async def _get_question(self, question_id: str):
        """Get question from database."""
        questions_table = get_table_name("questions")
        query = f"SELECT * FROM {questions_table} WHERE id = :question_id"
        row = await database.fetch_one(query, {"question_id": question_id})
        
        if not row:
            return None
        
        from models import Question
        return Question(**dict(row))
    
    async def _get_project(self, project_id: str):
        """Get project from database."""
        projects_table = get_table_name("projects")
        query = f"SELECT * FROM {projects_table} WHERE id = :project_id"
        row = await database.fetch_one(query, {"project_id": project_id})
        
        if not row:
            return None
        
        from models import Project
        return Project(**dict(row))
    
    async def _save_answer(self, answer: Answer):
        """Save answer to database."""
        answers_table = get_table_name("answers")
        query = f"""
            INSERT INTO {answers_table} 
            (id, question_id, text, confidence, created_at, updated_at)
            VALUES (:id, :question_id, :text, :confidence, :created_at, :updated_at)
        """
        
        await database.execute(query, {
            "id": str(answer.id),
            "question_id": str(answer.question_id),
            "text": answer.text,
            "confidence": float(answer.confidence),
            "created_at": answer.created_at.isoformat(),
            "updated_at": answer.updated_at.isoformat()
        })
    
    async def _save_source(self, source: Source):
        """Save source to database."""
        sources_table = get_table_name("sources")
        query = f"""
            INSERT INTO {sources_table} 
            (id, answer_id, file_name, file_path, page_number, document_id, relevance, text_content, created_at)
            VALUES (:id, :answer_id, :file_name, :file_path, :page_number, :document_id, :relevance, :text_content, :created_at)
        """
        
        await database.execute(query, {
            "id": str(source.id),
            "answer_id": str(source.answer_id),
            "file_name": source.file_name,
            "file_path": source.file_path,
            "page_number": source.page_number,
            "document_id": str(source.document_id) if source.document_id else None,
            "relevance": source.relevance,
            "text_content": source.text_content,
            "created_at": source.created_at.isoformat()
        })
    
    async def get_question_answers(self, question_id: str) -> List[Answer]:
        """Get all answers for a question."""
        answers_table = get_table_name("answers")
        query = f"""
            SELECT * FROM {answers_table} 
            WHERE question_id = :question_id 
            ORDER BY created_at DESC
        """
        rows = await database.fetch_all(query, {"question_id": question_id})
        return [Answer(**dict(row)) for row in rows]
    
    async def get_answer_sources(self, answer_id: str) -> List[Source]:
        """Get all sources for an answer."""
        sources_table = get_table_name("sources")
        query = f"""
            SELECT * FROM {sources_table} 
            WHERE answer_id = :answer_id 
            ORDER BY relevance DESC
        """
        rows = await database.fetch_all(query, {"answer_id": answer_id})
        return [Source(**dict(row)) for row in rows]


# Global service instance
response_generation_service = ResponseGenerationService()