"""
Project service for managing RFP projects, documents, questions, and answers.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timezone

from models import (
    Project, ProjectCreate, ProjectUpdate,
    Document, DocumentCreate,
    Question, QuestionCreate, Section,
    Answer, AnswerCreate, Source, SourceCreate, SourceData,
    ProjectIndex
)
from database_config import database, get_table_name

class ProjectService:
    """Service for project management operations."""
    
    def __init__(self):
        pass  # Database operations don't need instance variables
    
    # Project operations
    async def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new RFP project."""
        project = Project(
            **project_data.model_dump(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Insert into database
        projects_table = get_table_name("projects")
        query = f"""
            INSERT INTO {projects_table} (id, name, description, organization_id, created_at, updated_at)
            VALUES (:id, :name, :description, :organization_id, :created_at, :updated_at)
        """
        await database.execute(query, {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "organization_id": str(project.organization_id),
            "created_at": project.created_at,
            "updated_at": project.updated_at
        })
        
        return project
    
    async def get_projects(self, organization_id: Optional[UUID] = None) -> List[Project]:
        """Get all projects, optionally filtered by organization."""
        projects_table = get_table_name("projects")
        
        if organization_id:
            query = f"SELECT * FROM {projects_table} WHERE organization_id = :org_id ORDER BY created_at DESC"
            rows = await database.fetch_all(query, {"org_id": str(organization_id)})
        else:
            query = f"SELECT * FROM {projects_table} ORDER BY created_at DESC"
            rows = await database.fetch_all(query)
        
        return [Project(**dict(row)) for row in rows]
    
    async def get_project(self, project_id: UUID, include_relations: bool = False) -> Optional[Project]:
        """Get project by ID."""
        projects_table = get_table_name("projects")
        query = f"SELECT * FROM {projects_table} WHERE id = :project_id"
        row = await database.fetch_one(query, {"project_id": str(project_id)})
        
        if not row:
            return None
        
        return Project(**dict(row))
    
    async def update_project(self, project_id: UUID, update_data: ProjectUpdate) -> Optional[Project]:
        """Update project."""
        project = await self.get_project(project_id)
        if not project:
            return None
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.now()
        return project
    
    async def delete_project(self, project_id: UUID) -> bool:
        """Delete project and all related data."""
        project = await self.get_project(project_id)
        if not project:
            return False
        
        # Delete from database (cascade will handle related data)
        projects_table = get_table_name("projects")
        query = f"DELETE FROM {projects_table} WHERE id = :project_id"
        await database.execute(query, {"project_id": str(project_id)})
        
        return True
    
    # Document operations
    async def create_document(self, document_data: DocumentCreate) -> Document:
        """Create a new document record."""
        document = Document(
            **document_data.model_dump(),
            uploaded_at=datetime.now()
        )
        
        # Insert into database
        documents_table = get_table_name("documents")
        query = f"""
            INSERT INTO {documents_table} 
            (id, name, original_name, file_path, file_size, file_type, project_id, uploaded_at, status)
            VALUES (:id, :name, :original_name, :file_path, :file_size, :file_type, :project_id, :uploaded_at, :status)
        """
        await database.execute(query, {
            "id": str(document.id),
            "name": document.name,
            "original_name": document.original_name,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "file_type": document.file_type,
            "project_id": str(document.project_id),
            "uploaded_at": document.uploaded_at,
            "status": document.status
        })
        
        return document
    
    async def get_documents(self, project_id: UUID) -> List[Document]:
        """Get all documents for a project."""
        documents_table = get_table_name("documents")
        query = f"SELECT * FROM {documents_table} WHERE project_id = :project_id ORDER BY uploaded_at DESC"
        rows = await database.fetch_all(query, {"project_id": str(project_id)})
        return [Document(**dict(row)) for row in rows]
    
    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        documents_table = get_table_name("documents")
        query = f"SELECT * FROM {documents_table} WHERE id = :document_id"
        row = await database.fetch_one(query, {"document_id": str(document_id)})
        return Document(**dict(row)) if row else None
    
    async def update_document_status(self, document_id: UUID, status: str) -> Optional[Document]:
        """Update document processing status."""
        documents_table = get_table_name("documents")
        
        # Update status in database
        update_values = {"status": status}
        if status == "processed":
            update_values["processed_at"] = datetime.now()
        
        query = f"UPDATE {documents_table} SET status = :status"
        if "processed_at" in update_values:
            query += ", processed_at = :processed_at"
        query += " WHERE id = :document_id"
        
        await database.execute(query, {
            **update_values,
            "document_id": str(document_id)
        })
        
        return await self.get_document(document_id)
    
    # Question operations
    async def save_questions(self, project_id: UUID, sections: List[Section]) -> List[Question]:
        """Save extracted questions from RFP document."""
        saved_questions = []
        questions_table = get_table_name("questions")
        
        for section in sections:
            for question_data in section.questions:
                question = Question(
                    reference_id=question_data.reference_id,
                    text=question_data.text,
                    topic=question_data.topic,
                    section_title=section.title,
                    project_id=project_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Insert into database
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
                
                saved_questions.append(question)
        
        return saved_questions
    
    async def get_questions(self, project_id: UUID) -> List[Question]:
        """Get all questions for a project."""
        questions_table = get_table_name("questions")
        query = f"SELECT * FROM {questions_table} WHERE project_id = :project_id ORDER BY created_at ASC"
        rows = await database.fetch_all(query, {"project_id": str(project_id)})
        return [Question(**dict(row)) for row in rows]
    
    async def get_question(self, question_id: UUID) -> Optional[Question]:
        """Get question by ID."""
        questions_table = get_table_name("questions")
        query = f"SELECT * FROM {questions_table} WHERE id = :question_id"
        row = await database.fetch_one(query, {"question_id": str(question_id)})
        return Question(**dict(row)) if row else None
    
    async def get_questions_by_section(self, project_id: UUID) -> Dict[str, List[Question]]:
        """Get questions grouped by section."""
        questions = await self.get_questions(project_id)
        sections = {}
        
        for question in questions:
            section_title = question.section_title or "General"
            if section_title not in sections:
                sections[section_title] = []
            sections[section_title].append(question)
        
        return sections
    
    # Answer operations
    async def save_answer(self, answer_data: AnswerCreate, sources: List[SourceData] = None) -> Answer:
        """Save an AI-generated answer with sources."""
        answer = Answer(
            **answer_data.model_dump(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.answers.append(answer)
        
        # Save sources if provided
        if sources:
            for source_data in sources:
                try:
                    # Create Source manually field by field
                    source = Source(
                        id=UUID("00000000-0000-0000-0000-000000000000"),  # Let it generate
                        answer_id=answer.id,
                        file_name=source_data.file_name or "",
                        file_path=source_data.file_path,
                        page_number=source_data.page_number,
                        document_id=source_data.document_id,
                        relevance=source_data.relevance,
                        text_content=source_data.text_content,
                        created_at=datetime.now()
                    )
                    # Override the generated id
                    source.id = UUID(str(uuid4()))
                    self.sources.append(source)
                except Exception as e:
                    print(f"DEBUG: Error creating Source: {e}")
                    # Skip problematic sources for now
                    continue
        
        return answer
    
    async def get_answer(self, question_id: UUID) -> Optional[Answer]:
        """Get answer for a question from database."""
        try:
            answers_table = get_table_name("answers")
            query = f"SELECT * FROM {answers_table} WHERE question_id = :question_id ORDER BY created_at DESC LIMIT 1"
            row = await database.fetch_one(query, {"question_id": str(question_id)})
            
            if not row:
                return None
                
            return Answer(**dict(row))
        except Exception as e:
            print(f"Error getting answer: {e}")
            return None
    
    async def get_answer_with_sources(self, question_id: UUID) -> Optional[Dict[str, Any]]:
        """Get answer with its sources from database."""
        try:
            # Get the answer
            answer = await self.get_answer(question_id)
            if not answer:
                return None
            
            # For now, sources are not stored in database but returned in the generation metadata
            # In a production system, you would query a separate sources table here
            sources = []
            
            return {
                "answer": {
                    "id": answer.id,
                    "text": answer.text,
                    "confidence": answer.confidence,
                    "created_at": answer.created_at,
                    "updated_at": answer.updated_at
                },
                "sources": sources
            }
        except Exception as e:
            print(f"Error getting answer with sources: {e}")
            return None
    
    async def get_all_answers(self, project_id: UUID) -> Dict[UUID, Dict[str, Any]]:
        """Get all answers for a project with sources."""
        questions = await self.get_questions(project_id)
        results = {}
        
        for question in questions:
            answer_data = await self.get_answer_with_sources(question.id)
            if answer_data:
                results[question.id] = {
                    "question": question,
                    "answer": answer_data["answer"],
                    "sources": answer_data["sources"]
                }
        
        return results
    
    # Project Index operations (LlamaCloud integration)
    async def add_project_index(self, project_id: UUID, index_id: str, index_name: str) -> ProjectIndex:
        """Add a new index to a project."""
        project_index = ProjectIndex(
            project_id=project_id,
            index_id=index_id,
            index_name=index_name,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.project_indexes.append(project_index)
        return project_index
    
    async def get_project_indexes(self, project_id: UUID) -> List[ProjectIndex]:
        """Get all indexes for a project."""
        return [pi for pi in self.project_indexes if pi.project_id == project_id]
    
    async def remove_project_index(self, project_id: UUID, index_id: str) -> bool:
        """Remove an index from a project."""
        original_count = len(self.project_indexes)
        self.project_indexes = [
            pi for pi in self.project_indexes 
            if not (pi.project_id == project_id and pi.index_id == index_id)
        ]
        return len(self.project_indexes) < original_count
    
    # Statistics and analytics
    async def get_project_stats(self, project_id: UUID) -> Dict[str, Any]:
        """Get project statistics."""
        documents = await self.get_documents(project_id)
        questions = await self.get_questions(project_id)
        
        # Get answers from database
        answers_table = get_table_name("answers")
        question_ids = [str(q.id) for q in questions]
        
        if question_ids:
            placeholders = ','.join([f':qid_{i}' for i in range(len(question_ids))])
            query = f"SELECT * FROM {answers_table} WHERE question_id IN ({placeholders})"
            params = {f'qid_{i}': qid for i, qid in enumerate(question_ids)}
            answer_rows = await database.fetch_all(query, params)
            answers = [Answer(**dict(row)) for row in answer_rows]
        else:
            answers = []
        
        # Calculate last activity - handle timezone-naive datetimes consistently
        last_activity = datetime.min
        
        # Collect all datetimes and ensure they're all timezone-naive for comparison
        all_times = [last_activity]
        
        if questions:
            for q in questions:
                if q.updated_at:
                    # Convert to timezone-naive if needed
                    if q.updated_at.tzinfo is not None:
                        all_times.append(q.updated_at.replace(tzinfo=None))
                    else:
                        all_times.append(q.updated_at)
        
        if answers:
            for a in answers:
                if a.updated_at:
                    # Convert to timezone-naive if needed
                    if a.updated_at.tzinfo is not None:
                        all_times.append(a.updated_at.replace(tzinfo=None))
                    else:
                        all_times.append(a.updated_at)
        
        # Find the maximum time
        if len(all_times) > 1:
            last_activity = max(all_times)
        
        return {
            "total_documents": len(documents),
            "total_questions": len(questions),
            "answered_questions": len(answers),
            "completion_rate": len(answers) / len(questions) if questions else 0,
            "processed_documents": len([d for d in documents if d.status == "processed"]),
            "last_activity": last_activity
        }
    
    async def delete_answer(self, answer_id: UUID) -> bool:
        """Delete an answer by ID."""
        try:
            answers_table = get_table_name("answers")
            
            # Check if answer exists
            check_query = f"SELECT id FROM {answers_table} WHERE id = :answer_id"
            existing = await database.fetch_one(check_query, {"answer_id": str(answer_id)})
            
            if not existing:
                return False
            
            # Delete the answer
            delete_query = f"DELETE FROM {answers_table} WHERE id = :answer_id"
            await database.execute(delete_query, {"answer_id": str(answer_id)})
            
            print(f"[SUCCESS] Deleted answer: {answer_id}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to delete answer {answer_id}: {e}")
            return False


# Global service instance
project_service = ProjectService()
