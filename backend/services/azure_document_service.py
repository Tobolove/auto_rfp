"""
Azure Document Intelligence Service for parsing and analyzing documents.
Replaces LlamaCloud document parsing capabilities.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Union
from uuid import UUID
from pathlib import Path
import aiofiles
from datetime import datetime

from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, ContentFormat
from azure.identity.aio import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob.aio import BlobServiceClient
import openai

from ..models import Document, Section, Question, QuestionCreate

logger = logging.getLogger(__name__)

class AzureDocumentService:
    """
    Azure Document Intelligence service for parsing and analyzing documents.
    
    Features:
    - Document parsing with Azure Document Intelligence
    - Blob storage integration for file management
    - Question extraction from RFP documents
    - Structured content analysis
    """
    
    def __init__(
        self,
        document_intelligence_endpoint: str,
        storage_account_url: str,
        credential: Optional[TokenCredential] = None,
        openai_client: Optional[openai.AsyncOpenAI] = None
    ):
        """
        Initialize Azure Document Service.
        
        Args:
            document_intelligence_endpoint: Azure Document Intelligence endpoint
            storage_account_url: Azure Storage account URL
            credential: Azure credential (defaults to Managed Identity)
            openai_client: OpenAI client for AI operations
        """
        self.credential = credential or DefaultAzureCredential()
        self.document_intelligence_endpoint = document_intelligence_endpoint
        self.storage_account_url = storage_account_url
        self.openai_client = openai_client
        
        # Initialize clients
        self._doc_intelligence_client = None
        self._blob_service_client = None
    
    async def _get_document_intelligence_client(self) -> DocumentIntelligenceClient:
        """Get or create Document Intelligence client."""
        if not self._doc_intelligence_client:
            self._doc_intelligence_client = DocumentIntelligenceClient(
                endpoint=self.document_intelligence_endpoint,
                credential=self.credential
            )
        return self._doc_intelligence_client
    
    async def _get_blob_service_client(self) -> BlobServiceClient:
        """Get or create Blob Service client."""
        if not self._blob_service_client:
            self._blob_service_client = BlobServiceClient(
                account_url=self.storage_account_url,
                credential=self.credential
            )
        return self._blob_service_client
    
    async def parse_document(
        self,
        file_path: str,
        document_id: UUID,
        container_name: str = "documents"
    ) -> Dict[str, Any]:
        """
        Parse document using Azure Document Intelligence.
        
        Args:
            file_path: Path to the document file
            document_id: Unique document identifier
            container_name: Blob storage container name
        
        Returns:
            Parsed document content with structure and metadata
        """
        try:
            # Upload document to blob storage first
            blob_url = await self._upload_to_blob_storage(
                file_path, str(document_id), container_name
            )
            
            # Analyze document with Azure Document Intelligence
            doc_client = await self._get_document_intelligence_client()
            
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()
            
            # Use the comprehensive layout model for detailed analysis
            poller = await doc_client.begin_analyze_document(
                model_id="prebuilt-layout",
                analyze_request=AnalyzeDocumentRequest(bytes_source=file_content),
                content_format=ContentFormat.MARKDOWN
            )
            
            result = await poller.result()
            
            # Extract structured content
            parsed_content = {
                "document_id": str(document_id),
                "blob_url": blob_url,
                "content": result.content,
                "pages": [],
                "tables": [],
                "sections": [],
                "metadata": {
                    "page_count": len(result.pages) if result.pages else 0,
                    "language": result.languages[0].locale if result.languages else "en-US",
                    "model_version": result.model_id,
                    "analyzed_at": datetime.now().isoformat()
                }
            }
            
            # Process pages
            if result.pages:
                for page in result.pages:
                    page_info = {
                        "page_number": page.page_number,
                        "width": page.width,
                        "height": page.height,
                        "unit": page.unit,
                        "words": len(page.words) if page.words else 0,
                        "lines": len(page.lines) if page.lines else 0
                    }
                    parsed_content["pages"].append(page_info)
            
            # Process tables
            if result.tables:
                for table in result.tables:
                    table_info = {
                        "row_count": table.row_count,
                        "column_count": table.column_count,
                        "content": table.content if hasattr(table, 'content') else "",
                        "bounding_regions": [
                            {
                                "page_number": region.page_number,
                                "polygon": region.polygon
                            } for region in table.bounding_regions
                        ] if table.bounding_regions else []
                    }
                    parsed_content["tables"].append(table_info)
            
            # Extract sections based on document structure
            sections = await self._extract_sections(result)
            parsed_content["sections"] = sections
            
            logger.info(f"Successfully parsed document {document_id}")
            return parsed_content
            
        except Exception as e:
            logger.error(f"Error parsing document {document_id}: {str(e)}")
            raise
    
    async def _upload_to_blob_storage(
        self,
        file_path: str,
        blob_name: str,
        container_name: str
    ) -> str:
        """Upload file to Azure Blob Storage."""
        try:
            blob_service = await self._get_blob_service_client()
            blob_client = blob_service.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            async with aiofiles.open(file_path, 'rb') as file:
                data = await file.read()
                await blob_client.upload_blob(data, overwrite=True)
            
            return blob_client.url
            
        except Exception as e:
            logger.error(f"Error uploading file to blob storage: {str(e)}")
            raise
    
    async def _extract_sections(self, analysis_result) -> List[Dict[str, Any]]:
        """Extract sections from document analysis result."""
        sections = []
        
        # Use paragraphs to identify sections
        if hasattr(analysis_result, 'paragraphs') and analysis_result.paragraphs:
            current_section = None
            
            for paragraph in analysis_result.paragraphs:
                # Check if this looks like a section header
                if self._is_section_header(paragraph):
                    if current_section:
                        sections.append(current_section)
                    
                    current_section = {
                        "title": paragraph.content.strip(),
                        "content": "",
                        "page_number": paragraph.bounding_regions[0].page_number if paragraph.bounding_regions else 1,
                        "subsections": []
                    }
                elif current_section:
                    current_section["content"] += f"\n{paragraph.content}"
                else:
                    # Content before first section
                    if not sections:
                        sections.append({
                            "title": "Introduction",
                            "content": paragraph.content,
                            "page_number": paragraph.bounding_regions[0].page_number if paragraph.bounding_regions else 1,
                            "subsections": []
                        })
            
            # Add the last section
            if current_section:
                sections.append(current_section)
        
        # Fallback: create sections based on pages if no clear structure
        if not sections and hasattr(analysis_result, 'pages'):
            for i, page in enumerate(analysis_result.pages):
                page_content = ""
                if page.lines:
                    page_content = "\n".join([line.content for line in page.lines])
                
                sections.append({
                    "title": f"Page {page.page_number}",
                    "content": page_content,
                    "page_number": page.page_number,
                    "subsections": []
                })
        
        return sections
    
    def _is_section_header(self, paragraph) -> bool:
        """Determine if a paragraph is likely a section header."""
        content = paragraph.content.strip()
        
        # Common section header patterns for RFPs
        header_patterns = [
            "SECTION",
            "PART",
            "CHAPTER",
            "SCOPE OF WORK",
            "REQUIREMENTS",
            "EVALUATION CRITERIA",
            "SUBMISSION",
            "TECHNICAL SPECIFICATIONS",
            "PROPOSAL FORMAT",
            "BACKGROUND",
            "OBJECTIVE"
        ]
        
        # Check if content matches header patterns
        content_upper = content.upper()
        for pattern in header_patterns:
            if pattern in content_upper:
                return True
        
        # Check if it's short and looks like a title
        if len(content) < 100 and (
            content.isupper() or
            content.istitle() or
            content.count('.') >= 2  # Numbered sections like "2.1.3"
        ):
            return True
        
        return False
    
    async def extract_questions_from_document(
        self,
        parsed_content: Dict[str, Any],
        project_id: UUID
    ) -> List[QuestionCreate]:
        """
        Extract questions from parsed document using AI.
        
        Args:
            parsed_content: Parsed document content from parse_document
            project_id: Project identifier
        
        Returns:
            List of extracted questions
        """
        if not self.openai_client:
            logger.warning("OpenAI client not configured, cannot extract questions")
            return []
        
        try:
            questions = []
            
            # Process each section to extract questions
            for section in parsed_content.get("sections", []):
                section_questions = await self._extract_questions_from_section(
                    section, project_id
                )
                questions.extend(section_questions)
            
            logger.info(f"Extracted {len(questions)} questions from document")
            return questions
            
        except Exception as e:
            logger.error(f"Error extracting questions: {str(e)}")
            return []
    
    async def _extract_questions_from_section(
        self,
        section: Dict[str, Any],
        project_id: UUID
    ) -> List[QuestionCreate]:
        """Extract questions from a document section using AI."""
        try:
            system_prompt = """
            You are an expert at analyzing RFP (Request for Proposal) documents and extracting questions that vendors need to answer.
            
            Analyze the provided section and identify:
            1. Direct questions (clearly stated with question marks)
            2. Requirements that need responses (statements requiring vendor action/response)
            3. Evaluation criteria that need to be addressed
            4. Technical specifications that require detailed responses
            
            For each identified question/requirement, provide:
            - The exact text of the question/requirement
            - A category (technical, commercial, administrative, etc.)
            - Priority level (high, medium, low)
            - Whether it requires a detailed response
            
            Return your response as a JSON array with this structure:
            [
                {
                    "text": "Question or requirement text",
                    "category": "technical|commercial|administrative|other",
                    "priority": "high|medium|low",
                    "requires_detailed_response": true|false,
                    "section_reference": "Section title"
                }
            ]
            """
            
            user_prompt = f"""
            Section Title: {section['title']}
            Section Content: {section['content'][:4000]}  # Limit content to avoid token limits
            
            Please extract all questions and requirements from this section.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            try:
                extracted_questions = json.loads(ai_response)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response as JSON: {ai_response}")
                return []
            
            # Convert to QuestionCreate models
            questions = []
            for q_data in extracted_questions:
                question = QuestionCreate(
                    text=q_data["text"],
                    section_title=section["title"],
                    section_content=section["content"][:500],  # Abbreviated content
                    page_number=section.get("page_number", 1),
                    project_id=project_id,
                    metadata={
                        "category": q_data.get("category", "other"),
                        "priority": q_data.get("priority", "medium"),
                        "requires_detailed_response": q_data.get("requires_detailed_response", True),
                        "extraction_method": "azure_ai",
                        "extracted_at": datetime.now().isoformat()
                    }
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error extracting questions from section '{section['title']}': {str(e)}")
            return []
    
    async def cleanup(self):
        """Cleanup resources."""
        if self._doc_intelligence_client:
            await self._doc_intelligence_client.close()
        if self._blob_service_client:
            await self._blob_service_client.close()
