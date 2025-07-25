"""
Test script for question extraction functionality.
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_question_extraction():
    """Test the question extraction endpoint."""
    print("Testing question extraction...")
    
    # First, create a test project
    project_data = {
        "name": "Test RFP Project",
        "description": "Test project for question extraction",
        "organization_id": "a88c391c-51ee-4f66-9e97-38dbad5dac59"  # Use existing org from port 8001
    }
    
    try:
        # Create project
        print("Creating test project...")
        project_response = requests.post(f"{BASE_URL}/projects", json=project_data, timeout=30)
        print(f"Project creation status: {project_response.status_code}")
        
        if project_response.status_code != 201:
            print(f"Project creation failed: {project_response.text}")
            return
        
        project = project_response.json()
        project_id = project["id"]
        print(f"Created project: {project_id}")
        
        # Upload a test document via the upload endpoint
        print("Uploading test document...")
        
        # Prepare file for upload
        with open("test_questions.txt", "rb") as f:
            files = {"file": ("test_questions.txt", f, "text/plain")}
            doc_response = requests.post(
                f"{BASE_URL}/projects/{project_id}/documents", 
                files=files, 
                timeout=30
            )
        
        print(f"Document upload status: {doc_response.status_code}")
        
        if doc_response.status_code != 201:
            print(f"Document upload failed: {doc_response.text}")
            return
        
        document = doc_response.json()
        document_id = document["id"]
        print(f"Uploaded document: {document_id}")
        
        # Wait a moment for processing
        import time
        time.sleep(2)
        
        # Test question extraction
        extraction_request = {
            "document_id": document_id,
            "project_id": project_id
        }
        
        print("Testing question extraction...")
        extract_response = requests.post(
            f"{BASE_URL}/ai/extract-questions", 
            json=extraction_request, 
            timeout=30
        )
        print(f"Extraction status: {extract_response.status_code}")
        print(f"Response: {extract_response.text}")
        
        if extract_response.status_code == 200:
            result = extract_response.json()
            print("SUCCESS: Question extraction completed!")
            print(f"Total questions: {result.get('total_questions', 0)}")
            print(f"Sections: {len(result.get('sections', []))}")
            for section in result.get('sections', []):
                print(f"  - {section.get('title')}: {len(section.get('questions', []))} questions")
        else:
            print(f"FAILED: {extract_response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_question_extraction()