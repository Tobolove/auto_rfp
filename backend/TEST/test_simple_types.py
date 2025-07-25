#!/usr/bin/env python3
"""
Simple test for document types endpoint
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_types():
    """Test the document types without heavy dependencies"""
    try:
        from models_reference import DocumentType, IndustryTag, CapabilityTag, ProjectSize, GeographicScope, ConfidenceLevel
        
        print("SUCCESS: Reference models imported successfully")
        
        # Test enum values
        doc_types = [{"value": dt.value, "label": dt.value.replace("_", " ").title()} for dt in DocumentType]
        industry_tags = [{"value": it.value, "label": it.value.replace("_", " ").title()} for it in IndustryTag]
        
        print(f"Document Types: {len(doc_types)} available")
        print(f"Industry Tags: {len(industry_tags)} available")
        
        # Show first few as examples
        print("\nExample Document Types:")
        for dt in doc_types[:3]:
            print(f"  - {dt['value']}: {dt['label']}")
            
        print("\nExample Industry Tags:")
        for it in industry_tags[:3]:
            print(f"  - {it['value']}: {it['label']}")
            
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_types()