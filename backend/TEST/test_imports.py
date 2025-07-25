"""
Test script to verify imports are working correctly.
"""

import sys
import os

# Configure Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing AutoRFP Backend imports...")
print(f"📁 Current directory: {os.getcwd()}")
print(f"🐍 Python path: {sys.path[0]}")

try:
    # Test config_path import
    import config_path
    print("✅ config_path imported successfully")
    
    # Test models import
    from models import Organization, User, Project
    print("✅ models imported successfully")
    
    # Test services import
    from services.organization_service import organization_service
    print("✅ organization_service imported successfully")
    
    from services.project_service import project_service
    print("✅ project_service imported successfully")
    
    from services.ai_service import ai_service
    print("✅ ai_service imported successfully")
    
    from services.qdrant_service_factory import get_qdrant_service
    print("✅ qdrant_service_factory imported successfully")
    
    # Test main app import
    from main import app
    print("✅ FastAPI app imported successfully")
    
    print("\n🎉 All imports successful! Backend should start without import errors.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔧 Troubleshooting suggestions:")
    print("1. Make sure you're in the backend directory")
    print("2. Install missing dependencies: pip install -r requirements.txt")
    print("3. Check Python path configuration")

except Exception as e:
    print(f"❌ Unexpected error: {e}")
