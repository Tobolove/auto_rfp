#!/usr/bin/env python3
"""
Test script to verify the project stats datetime fix
"""
import requests
import json

def test_project_stats():
    """Test project stats endpoint that was failing"""
    base_url = "http://localhost:8000"
    
    # Test the problematic project ID from the error
    project_id = "d611a6b3-0716-49cc-8c1b-7a273c8c99bb"
    
    print("🧪 Testing Project Stats Datetime Fix")
    print("=" * 50)
    
    try:
        response = requests.get(f"{base_url}/projects/{project_id}/stats")
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS: Project stats endpoint working!")
            print(f"📈 Stats: {json.dumps(data, indent=2, default=str)}")
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to backend server")
        print("💡 Make sure the backend is running on port 8000")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_project_stats()