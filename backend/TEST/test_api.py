"""
Quick test script to verify AutoRFP Backend API is working correctly.
Tests the most important endpoints after server startup.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_endpoint(url: str, method: str = "GET", data: dict = None, description: str = ""):
    """Test a single endpoint."""
    try:
        print(f"🧪 Testing: {description or url}")
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        
        if response.status_code in [200, 201]:
            print(f"✅ SUCCESS: {response.status_code}")
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
        else:
            print(f"⚠️  Status {response.status_code}: {response.text[:100]}...")
        
        print()
        return response.status_code in [200, 201]
        
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR: Server not running on {url}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all API tests."""
    print("🧪 AutoRFP Backend API Test Suite")
    print(f"🌐 Testing server at: {BASE_URL}")
    print(f"🕒 Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test basic endpoints
    tests = [
        (f"{BASE_URL}/", "GET", None, "Root endpoint - API welcome"),
        (f"{BASE_URL}/health", "GET", None, "Health check - All services status"),
        (f"{BASE_URL}/docs", "GET", None, "API Documentation"),
        (f"{BASE_URL}/qdrant/connection/test", "GET", None, "Qdrant connection test"),
        (f"{BASE_URL}/organizations", "GET", None, "List organizations"),
    ]
    
    successful_tests = 0
    total_tests = len(tests)
    
    for url, method, data, description in tests:
        if test_endpoint(url, method, data, description):
            successful_tests += 1
    
    print("=" * 60)
    print(f"🎯 Test Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 All tests passed! AutoRFP Backend is working correctly.")
        print()
        print("🌐 Available endpoints:")
        print(f"   • API Root: {BASE_URL}")
        print(f"   • API Docs: {BASE_URL}/docs")
        print(f"   • ReDoc: {BASE_URL}/redoc")
        print(f"   • Health: {BASE_URL}/health")
    else:
        print("⚠️  Some tests failed. Check the server logs for details.")
    
    print()

if __name__ == "__main__":
    main()
