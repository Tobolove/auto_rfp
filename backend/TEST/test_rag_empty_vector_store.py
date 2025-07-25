#!/usr/bin/env python3
"""
Test script for RAG Answer Generation System with Empty Vector Store
This script tests the RAG system when the vector store is empty,
ensuring it falls back gracefully to LLM-only responses.
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_answer_service import rag_answer_service
from models import GenerateResponseRequest

async def test_empty_vector_store():
    """Test RAG system with empty vector store."""
    print("🧪 Testing RAG System with Empty Vector Store")
    print("=" * 70)
    print(f"🕒 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Service Configuration Check
    print("\n🔧 Step 1: Service Configuration Check")
    print("-" * 40)
    
    openai_configured = rag_answer_service.openai_client is not None
    qdrant_configured = rag_answer_service.qdrant_client is not None
    embeddings_configured = rag_answer_service.embeddings is not None
    
    print(f"✅ Azure OpenAI Client: {'Configured' if openai_configured else 'Not Configured (will use mock)'}")
    print(f"✅ Qdrant Client: {'Configured' if qdrant_configured else 'Not Configured (will use mock)'}")
    print(f"✅ Embeddings: {'Configured' if embeddings_configured else 'Not Configured'}")
    print(f"✅ Collection Name: {rag_answer_service.collection_name}")
    print(f"✅ Max Context Chunks: {rag_answer_service.max_context_chunks}")
    print(f"✅ Min Similarity Score: {rag_answer_service.min_similarity_score}")
    
    # Test 2: Empty Vector Store Search
    print("\n🔍 Step 2: Testing Vector Store Search (Expected: Empty Results)")
    print("-" * 40)
    
    test_queries = [
        "What is your company's experience with cloud infrastructure projects?",
        "Describe your project management methodology and approach",
        "What are your security protocols and compliance certifications?",
        "Please provide details about your team's technical expertise",
        "What is your pricing model and cost structure?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 Query {i}: {query}")
        try:
            search_results = await rag_answer_service.search_knowledge_base(
                query=query,
                top_k=5
            )
            
            chunks_found = search_results.get('results_count', 0)
            print(f"   📊 Vector Search Results: {chunks_found} chunks found")
            
            if chunks_found == 0:
                print(f"   ✅ Expected: Empty vector store confirmed")
            else:
                print(f"   ⚠️  Unexpected: Found {chunks_found} chunks in supposedly empty store")
                for j, chunk in enumerate(search_results.get('chunks', [])[:2], 1):
                    print(f"      📄 Chunk {j}: Score {chunk.get('score', 0):.3f}")
                    
        except Exception as e:
            print(f"   ❌ Search Error: {e}")
    
    # Test 3: Answer Generation with Empty Vector Store
    print("\n🤖 Step 3: Testing Answer Generation (LLM Only)")
    print("-" * 40)
    
    rfp_questions = [
        {
            "question": "What is your company's experience with similar RFP projects in the technology sector?",
            "expected_type": "experience"
        },
        {
            "question": "Please describe your proposed approach and methodology for this project.",
            "expected_type": "approach"
        },
        {
            "question": "What is your proposed timeline and key milestones for project delivery?",
            "expected_type": "timeline"
        },
        {
            "question": "Please provide details about your team structure and key personnel qualifications.",
            "expected_type": "team"
        },
        {
            "question": "What is your total cost proposal and pricing structure for this engagement?",
            "expected_type": "cost"
        }
    ]
    
    successful_answers = 0
    total_questions = len(rfp_questions)
    
    for i, test_case in enumerate(rfp_questions, 1):
        question = test_case["question"]
        expected_type = test_case["expected_type"]
        
        print(f"\n🔤 Question {i}/{total_questions}: {question}")
        
        try:
            # Create request
            request = GenerateResponseRequest(
                question=question,
                question_id=f"test-question-{i}",
                project_id="test-project-empty-vectorstore",
                use_all_indexes=True
            )
            
            # Generate answer
            start_time = datetime.now()
            response = await rag_answer_service.generate_answer(request)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            
            # Analyze response
            answer_length = len(response.response)
            confidence = response.metadata.get('confidence', 0)
            search_method = response.metadata.get('search_method', 'unknown')
            sources_count = len(response.sources)
            context_chunks = response.metadata.get('context_chunks_used', 0)
            
            print(f"   ✅ Answer Generated Successfully!")
            print(f"   ⏱️  Generation Time: {duration:.2f} seconds")
            print(f"   📝 Answer Length: {answer_length} characters")
            print(f"   🎯 Confidence Score: {confidence:.2f}")
            print(f"   🔧 Search Method: {search_method}")
            print(f"   📚 Sources Found: {sources_count}")
            print(f"   📊 Context Chunks Used: {context_chunks}")
            
            # Check if it's using mock/fallback
            if context_chunks == 0 and search_method in ['mock', 'qdrant_rag']:
                print(f"   ✅ Correctly using LLM-only mode (no vector context)")
            
            # Show answer preview
            answer_preview = response.response[:200] + "..." if len(response.response) > 200 else response.response
            print(f"   📄 Answer Preview:")
            print(f"      {answer_preview}")
            
            # Check for template response indicators
            if "template response" in response.response.lower():
                print(f"   📋 Response Type: Template/Mock (expected for empty vector store)")
            elif answer_length > 100:
                print(f"   🤖 Response Type: Generated (good LLM response)")
            
            successful_answers += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   🔍 Error Type: {type(e).__name__}")
    
    # Test 4: Performance and Reliability Summary
    print(f"\n📊 Step 4: Test Results Summary")
    print("-" * 40)
    
    success_rate = (successful_answers / total_questions) * 100
    print(f"✅ Success Rate: {successful_answers}/{total_questions} ({success_rate:.1f}%)")
    
    if success_rate >= 100:
        print(f"🎉 EXCELLENT: All questions answered successfully!")
    elif success_rate >= 80:
        print(f"✅ GOOD: Most questions answered successfully")
    elif success_rate >= 60:
        print(f"⚠️  FAIR: Some issues with answer generation")
    else:
        print(f"❌ POOR: Significant issues with answer generation")
    
    # Test 5: Configuration Recommendations
    print(f"\n⚙️  Step 5: Configuration Status & Recommendations")
    print("-" * 40)
    
    if not openai_configured:
        print(f"⚠️  Azure OpenAI not configured:")
        print(f"   📝 Set AZURE_OPENAI_ENDPOINT environment variable")
        print(f"   🔑 Set AZURE_OPENAI_API_KEY environment variable") 
        print(f"   🎯 Current behavior: Using mock responses")
    else:
        print(f"✅ Azure OpenAI configured - Real LLM responses available")
    
    if not qdrant_configured:
        print(f"⚠️  Qdrant not configured:")
        print(f"   🔗 Set QDRANT_URL environment variable")
        print(f"   🔑 Set QDRANT_API_KEY environment variable")
        print(f"   🎯 Current behavior: No vector search, LLM-only mode")
    else:
        print(f"✅ Qdrant configured - Vector search available")
        print(f"   📊 Collection: {rag_answer_service.collection_name}")
        print(f"   💡 Next step: Upload documents to populate vector store")
    
    # Test 6: API Endpoint Test
    print(f"\n🌐 Step 6: API Integration Test")
    print("-" * 40)
    
    print(f"📡 To test via API endpoints:")
    print(f"   🔧 Test RAG system:")
    print(f"      POST http://localhost:8000/ai/test-rag")
    print(f"      {{\"query\": \"What is your experience with similar projects?\"}}")
    print(f"")
    print(f"   🤖 Generate answer:")
    print(f"      POST http://localhost:8000/ai/generate-response")
    print(f"      {{")
    print(f"        \"question\": \"What is your company experience?\",")
    print(f"        \"question_id\": \"test-123\",")
    print(f"        \"project_id\": \"test-project\",")
    print(f"        \"use_all_indexes\": true")
    print(f"      }}")
    
    print("\n" + "=" * 70)
    print(f"🎯 RAG System Test with Empty Vector Store: COMPLETED")
    print(f"🕒 Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if successful_answers == total_questions:
        print("🎉 RESULT: System working correctly in LLM-only mode!")
        print("💡 Ready to populate vector store with your company documents.")
    else:
        print("⚠️  RESULT: Some issues detected. Check configuration above.")

async def main():
    """Run the empty vector store test."""
    print("🚀 Starting RAG System Test with Empty Vector Store...")
    print("This test verifies the system works correctly before adding documents.\n")
    
    try:
        await test_empty_vector_store()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with unexpected error: {e}")
        import traceback
        print(f"📋 Full traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())