"""
Test Section model creation and serialization.
"""

from models import Section, Question, ExtractQuestionsResponse
import uuid
from datetime import datetime

def test_section_creation():
    """Test creating Section objects and response."""
    
    # Create a test question
    question = Question(
        id=uuid.uuid4(),
        text="What is your company's experience?",
        topic="Experience",
        section_title="Company Background",
        project_id=uuid.uuid4(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create a test section
    section = Section(
        id=str(uuid.uuid4()),
        title="Company Background",
        description="Questions about company experience",
        questions=[question]
    )
    
    print(f"Section created: {section}")
    print(f"Section dict: {section.model_dump()}")
    
    # Test response creation
    response = ExtractQuestionsResponse(
        document_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        total_questions=1,
        sections=[section],
        processing_time=1.0,
        extraction_method="test"
    )
    
    print(f"Response created: {response}")
    print(f"Response dict: {response.model_dump()}")

if __name__ == "__main__":
    test_section_creation()