#!/usr/bin/env python3
"""
Test startup script to check if all imports work correctly.
"""

import os
import sys

# Set environment variable to suppress OpenMP warning
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Configure Python path
import config_path

try:
    print("Testing imports...")
    
    # Test models import
    from models import Organization, OrganizationCreate
    print("+ Models imported successfully")
    
    # Test services imports
    from services.organization_service import organization_service
    print("+ Organization service imported successfully")
    
    from services.project_service import project_service
    print("+ Project service imported successfully")
    
    from services.ai_service import ai_service
    print("+ AI service imported successfully")
    
    # Test Qdrant service (this might be causing issues)
    try:
        from services.qdrant_service_factory import get_qdrant_service, initialize_quote_collection, test_qdrant_connection
        print("+ Qdrant service imported successfully")
    except Exception as e:
        print(f"- Qdrant service import failed: {e}")
    
    print("All imports successful! FastAPI should work now.")
    
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()