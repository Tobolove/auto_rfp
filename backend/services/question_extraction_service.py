"""
AI-powered question extraction service for RFP documents.
Uses Azure OpenAI to automatically extract questions from uploaded RFP documents.
"""
import os
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from openai import AsyncAzureOpenAI
from models import Question, Section, ExtractQuestionsRequest, ExtractQuestionsResponse
from database_config import database, get_table_name


class QuestionExtractionService:
    """Service for extracting questions from RFP documents using AI."""
    
    def __init__(self):
        # Azure OpenAI setup
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = "gpt-4"  # Adjust based on your deployment
        
        # Temporarily disable Azure OpenAI to test mock path
        # if self.azure_endpoint and self.azure_key:
        #     self.client = AsyncAzureOpenAI(
        #         azure_endpoint=self.azure_endpoint,
        #         api_key=self.azure_key,
        #         api_version="2024-02-15-preview"
        #     )
        # else:
        self.client = None
        print("DEBUG: Temporarily using mock responses to isolate issue")
    
    async def extract_questions_from_document(self, request: ExtractQuestionsRequest) -> ExtractQuestionsResponse:
        """Extract questions from an RFP document."""
        print(f"DEBUG: Starting extraction for document {request.document_id}, project {request.project_id}")
        try:
            # Get document content
            from services.document_service import document_service
            print(f"DEBUG: Getting document from service...")
            document = await document_service.get_document(str(request.document_id))
            print(f"DEBUG: Document retrieved: {document.name if document else 'None'}")
            
            if not document:
                raise ValueError(f"Document {request.document_id} not found")
            
            if document.status != "processed":
                raise ValueError(f"Document {document.name} is not yet processed")
            
            # Read document content (this should be stored during processing)
            document_text = await self._get_document_text(document.file_path)
            
            print(f"DEBUG: Extracted text length: {len(document_text) if document_text else 0}")
            print(f"DEBUG: First 200 chars: {repr(document_text[:200]) if document_text else 'None'}")
            
            if not document_text or len(document_text.strip()) < 50:
                raise ValueError(f"Document {document.name} has insufficient content for processing (got {len(document_text.strip()) if document_text else 0} characters)")
            
            # Extract questions using AI
            if self.client:
                print(f"Using Azure OpenAI for extraction (client configured)")
                sections = await self._extract_with_azure_openai(document_text)
            else:
                print(f"Using mock extraction (no Azure OpenAI client)")
                sections = await self._extract_with_mock(document_text)
            
            # Save questions to database
            await self._save_questions(str(request.project_id), sections)
            
            print(f"Creating response with {len(sections)} sections")
            for i, section in enumerate(sections):
                print(f"Section {i}: id={getattr(section, 'id', 'MISSING')}, title={section.title}, questions={len(section.questions)}")
            
            response = ExtractQuestionsResponse(
                document_id=request.document_id,
                project_id=request.project_id,
                total_questions=sum(len(section.questions) for section in sections),
                sections=sections,
                processing_time=2.5,  # Placeholder
                extraction_method="azure_openai" if self.client else "mock"
            )
            print(f"Response created successfully")
            return response
            
        except Exception as e:
            print(f"Question extraction failed: {e}")
            raise
    
    async def _get_document_text(self, file_path: str) -> str:
        """Get text content from processed document."""
        from pathlib import Path
        from services.document_service import document_service
        from services.file_storage_service import file_storage_service
        
        try:
            # Get file content using the file storage service
            file_content = await file_storage_service.get_document(file_path)
            
            if file_content:
                # If it's a text file, decode and return
                if file_path.lower().endswith('.txt'):
                    return file_content.decode('utf-8')
                else:
                    # For other file types, use document service extraction
                    # First save to temp file
                    import tempfile
                    import os
                    
                    file_extension = Path(file_path).suffix.lower()
                    with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                        temp_file.write(file_content)
                        temp_path = temp_file.name
                    
                    try:
                        text = await document_service._simple_text_extraction(Path(temp_path), file_extension)
                        return text
                    finally:
                        # Clean up temp file
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
            else:
                return f"[Unable to retrieve file content from {file_path}]"
                
        except Exception as e:
            print(f"Text extraction failed for {file_path}: {e}")
            return f"[Unable to extract text from {file_path}]"
    
    async def _extract_with_azure_openai(self, document_text: str) -> List[Section]:
        """Extract questions using Azure OpenAI."""
        
        system_prompt = """You are an expert at analyzing RFP (Request for Proposal) documents and extracting key questions that need to be answered by bidding companies.

Your task is to:
1. Read through the RFP document carefully
2. Identify all questions, requirements, and requests for information
3. Group related questions into logical sections
4. For each question, determine the topic/category and section title
5. Return a structured JSON response

Focus on:
- Direct questions (What is your experience with...)
- Requirements that need responses (Provide details about...)
- Information requests (Describe your approach to...)
- Compliance requirements that need confirmation
- Technical specifications that need responses

Return the response in this exact JSON format:
{
  "sections": [
    {
      "title": "Section Title",
      "description": "Brief description of this section",
      "questions": [
        {
          "text": "The actual question or requirement",
          "topic": "Category/topic of the question",
          "reference_id": "Unique identifier if provided in RFP"
        }
      ]
    }
  ]
}"""

        user_prompt = f"""Please analyze this RFP document and extract all questions and requirements that need responses:

{document_text[:8000]}  # Limit to avoid token limits

Return the structured JSON response with all identified questions grouped into appropriate sections."""

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            
            # Extract JSON from the response (in case it's wrapped in markdown)
            json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content
            
            data = json.loads(json_str)
            
            # Convert to Section objects
            sections = []
            for section_data in data.get("sections", []):
                questions = []
                for q_data in section_data.get("questions", []):
                    question = Question(
                        id=uuid.uuid4(),
                        text=q_data["text"],
                        topic=q_data["topic"],
                        reference_id=q_data.get("reference_id"),
                        section_title=section_data["title"],
                        project_id=uuid.uuid4(),  # Will be set properly later
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    questions.append(question)
                
                section = Section(
                    id=str(uuid.uuid4()),
                    title=section_data["title"],
                    description=section_data.get("description", ""),
                    questions=questions
                )
                sections.append(section)
            
            return sections
            
        except Exception as e:
            print(f"Azure OpenAI extraction failed: {e}")
            print(f"Azure OpenAI response content: {content if 'content' in locals() else 'No response received'}")
            # Fallback to mock extraction
            return await self._extract_with_mock(document_text)
    
    async def _extract_with_mock(self, document_text: str) -> List[Section]:
        """Mock question extraction for development/testing."""
        
        print(f"DEBUG: Mock extraction analyzing document with {len(document_text)} characters")
        print(f"DEBUG: Document content preview: {repr(document_text[:500])}")
        
        # Enhanced pattern-based extraction
        question_patterns = [
            r"(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:Question\s*\d*:?\s*)?(what\s+(?:is|are|would|should|will|do|does)[^.?]*\?)",
            r"(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:Question\s*\d*:?\s*)?(how\s+(?:do|does|would|should|will|can|many|much)[^.?]*\?)",
            r"(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:Question\s*\d*:?\s*)?(please\s+(?:provide|describe|explain|list|detail)[^.?]*[.?])",
            r"(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:Question\s*\d*:?\s*)?(describe\s+your[^.?]*[.?])",
            r"(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(?:Question\s*\d*:?\s*)?(provide\s+(?:details|information|examples)[^.?]*[.?])",
            r"(?i)(?:^|\n)\s*(?:\d+\.?\s*)?(.+\?)",  # Any line ending with ?
        ]
        
        questions = []
        for pattern in question_patterns:
            matches = re.findall(pattern, document_text, re.MULTILINE)
            for match in matches:
                # Extract the actual question text (may be in a group)
                question_text = match if isinstance(match, str) else match[0] if match else ""
                question_text = question_text.strip()
                
                # Filter out short or non-meaningful questions
                if len(question_text) > 10 and not question_text.lower().startswith(('yes', 'no', 'true', 'false')):
                    # Clean up the question
                    question_text = re.sub(r'^(?:\d+\.?\s*)?(?:Question\s*\d*:?\s*)?', '', question_text, flags=re.IGNORECASE)
                    questions.append(question_text.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_questions = []
        for q in questions:
            if q.lower() not in seen:
                seen.add(q.lower())
                unique_questions.append(q)
        
        questions = unique_questions[:15]  # Limit to reasonable number
        
        print(f"DEBUG: Found {len(questions)} questions from patterns:")
        for i, q in enumerate(questions, 1):
            print(f"  {i}. {q}")
        
        # If still no patterns found, analyze by lines and look for question-like content
        if not questions:
            print("DEBUG: No regex matches, trying line-by-line analysis")
            lines = document_text.split('\n')
            for line in lines:
                line = line.strip()
                if (len(line) > 15 and 
                    (line.endswith('?') or 
                     any(word in line.lower() for word in ['what', 'how', 'please', 'describe', 'provide', 'explain']) or
                     'question' in line.lower())):
                    questions.append(line)
            
            # Still nothing? Use document-aware fallback
            if not questions:
                print("DEBUG: Still no questions found, using document-aware fallback")
                # Try to create questions based on document content keywords
                doc_lower = document_text.lower()
                if 'rfp' in doc_lower or 'request for proposal' in doc_lower:
                    questions = [
                        "What is your experience with projects similar to those described in this RFP?",
                        "Please describe your proposed approach for this project.",
                        "What is your proposed timeline and key milestones?",
                        "Please provide information about your team and qualifications.",
                        "What is your pricing structure for this project?"
                    ]
                else:
                    # Generic fallback
                    questions = [
                        f"Please provide details about the content described in this document.",
                        f"What is your experience with the topics covered in this document?",
                        f"How would you approach the requirements outlined in this document?"
                    ]
        
        # Group into sections
        sections = []
        
        # Company Experience Section
        experience_questions = [q for q in questions if any(word in q.lower() for word in ['experience', 'background', 'history', 'previous'])]
        if experience_questions:
            section_questions = []
            for q_text in experience_questions:
                question = Question(
                    id=uuid.uuid4(),
                    text=q_text,
                    topic="Company Experience",
                    section_title="Company Background and Experience",
                    project_id=uuid.uuid4(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                section_questions.append(question)
            
            section_id = str(uuid.uuid4())
            print(f"DEBUG: Creating Company Background section with id={section_id}")
            section = Section(
                id=section_id,
                title="Company Background and Experience",
                description="Questions about your company's qualifications and experience",
                questions=section_questions
            )
            print(f"DEBUG: Section created: {section}")
            sections.append(section)
        
        # Technical Approach Section
        technical_questions = [q for q in questions if any(word in q.lower() for word in ['approach', 'method', 'technical', 'solution', 'design'])]
        if not technical_questions:
            technical_questions = [q for q in questions if q not in experience_questions][:3]
        
        if technical_questions:
            section_questions = []
            for q_text in technical_questions:
                question = Question(
                    id=uuid.uuid4(),
                    text=q_text,
                    topic="Technical Approach",
                    section_title="Technical Approach and Methodology",
                    project_id=uuid.uuid4(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                section_questions.append(question)
            
            sections.append(Section(
                id=str(uuid.uuid4()),
                title="Technical Approach and Methodology",
                description="Questions about your proposed technical solution",
                questions=section_questions
            ))
        
        # Project Management Section
        remaining_questions = [q for q in questions if q not in experience_questions and q not in technical_questions]
        if remaining_questions:
            section_questions = []
            for q_text in remaining_questions:
                question = Question(
                    id=uuid.uuid4(),
                    text=q_text,
                    topic="Project Management",
                    section_title="Project Management and Delivery",
                    project_id=uuid.uuid4(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                section_questions.append(question)
            
            sections.append(Section(
                id=str(uuid.uuid4()),
                title="Project Management and Delivery",
                description="Questions about project timeline, resources, and delivery",
                questions=section_questions
            ))
        
        return sections
    
    async def _save_questions(self, project_id: str, sections: List[Section]):
        """Save extracted questions to the database."""
        questions_table = get_table_name("questions")
        
        for section in sections:
            for question in section.questions:
                # Update the project_id
                question.project_id = uuid.UUID(project_id)
                
                query = f"""
                    INSERT INTO {questions_table} 
                    (id, reference_id, text, topic, section_title, project_id, created_at, updated_at)
                    VALUES (:id, :reference_id, :text, :topic, :section_title, :project_id, :created_at, :updated_at)
                """
                
                await database.execute(query, {
                    "id": str(question.id),
                    "reference_id": question.reference_id,
                    "text": question.text,
                    "topic": question.topic,
                    "section_title": question.section_title,
                    "project_id": str(question.project_id),
                    "created_at": question.created_at,
                    "updated_at": question.updated_at
                })
    
    async def get_project_questions(self, project_id: str) -> List[Question]:
        """Get all questions for a project."""
        questions_table = get_table_name("questions")
        query = f"""
            SELECT * FROM {questions_table} 
            WHERE project_id = :project_id 
            ORDER BY section_title, created_at
        """
        rows = await database.fetch_all(query, {"project_id": project_id})
        return [Question(**dict(row)) for row in rows]


# Global service instance
question_extraction_service = QuestionExtractionService()