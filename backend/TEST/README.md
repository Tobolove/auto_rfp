# TEST Directory

This directory contains all test scripts, utility scripts, and test data files for the RFP AI backend.

## 📂 Directory Structure

### Test Scripts
- `test_api.py` - API endpoint testing
- `test_imports.py` - Import verification
- `test_db_connection.py` - Database connection testing
- `test_question_extraction.py` - Question extraction functionality
- `test_rag_system.py` - RAG system testing
- `test_org_service.py` - Organization service testing
- `test_server.py` - Server functionality testing
- `test_startup.py` - Startup process testing

### Utility Scripts
- `fix_qdrant_collection.py` - Qdrant collection repair utility
- `vivavis.py` - Vivavis RAG agent example
- `DOCLOADER.py` - Document loader utility
- `restart_server.py` - Server restart utility

### Test Data Files
- `test_*.txt` - Various test text files
- `test_*.xlsx` - Test Excel files
- `test_rfp_document.txt` - Sample RFP document
- `test_questions.txt` - Sample question sets

## 🧪 Running Tests

### Individual Tests
```bash
# Test API endpoints
python TEST/test_api.py

# Test imports
python TEST/test_imports.py

# Test RAG system
python TEST/test_rag_system.py
```

### Database Tests
```bash
# Test database connection
python TEST/test_db_connection.py

# Test organization service
python TEST/test_org_service.py
```

### AI System Tests
```bash
# Test question extraction
python TEST/test_question_extraction.py

# Test RAG system
python TEST/test_rag_system.py
```

## 🔧 Utility Scripts

### Fix Qdrant Collection
```bash
python TEST/fix_qdrant_collection.py
```

### Vivavis RAG Agent (Example)
```bash
python TEST/vivavis.py
```

## 📝 Notes

- All test scripts assume the main server is running on `localhost:8000`
- Make sure to configure your `.env` file before running tests
- Some tests require specific test data to be present in the database
- For integration tests, ensure all services (database, Qdrant, Azure OpenAI) are accessible

## 🚀 Quick Test Suite

To run a basic health check of the system:

1. `python TEST/test_imports.py` - Verify all imports work
2. `python TEST/test_db_connection.py` - Check database connectivity  
3. `python TEST/test_api.py` - Test basic API functionality
4. `python TEST/test_rag_system.py` - Verify RAG system works