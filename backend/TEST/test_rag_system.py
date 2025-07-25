#!/usr/bin/env python3
"""
Test script for RAG Answer Generation System
"""

import asyncio
import sys
import os
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_answer_service import rag_answer_service
from models import GenerateResponseRequest

async def test_rag_system():
    """Test the RAG-based answer generation system."""
    print("🧪 Testing RAG Answer Generation System")
    print("=" * 60)
    
    # Test 1: Check service initialization
    print("\n🔧 Testing Service Initialization...")
    print(f"✅ Azure OpenAI configured: {rag_answer_service.openai_client is not None}")
    print(f"✅ Qdrant configured: {rag_answer_service.qdrant_client is not None}")
    print(f"✅ Embeddings configured: {rag_answer_service.embeddings is not None}")
    print(f"✅ Collection name: {rag_answer_service.collection_name}")
    
    # Test 2: Search knowledge base
    print("\n🔍 Testing Knowledge Base Search...")
    test_queries = [
        "What is your experience with similar projects?",
        "Please describe your proposed approach and methodology",
        "What is your team structure and key personnel?",
        "How do you ensure project quality and deliverables?"
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        try:
            results = await rag_answer_service.search_knowledge_base(
                query=query,
                top_k=3
            )
            
            print(f"   📊 Results: {results['results_count']} chunks found")
            if results['chunks']:
                for i, chunk in enumerate(results['chunks'][:2], 1):
                    print(f"   📄 Chunk {i}: Score {chunk['score']:.3f} - {chunk['content'][:100]}...")
            else:
                print("   ⚠️  No relevant chunks found")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test 3: Generate full answers
    print("\n🤖 Testing Answer Generation...")
    
    test_request = GenerateResponseRequest(
        question="What is your company's experience with similar RFP projects?",
        question_id="test-question-1",
        project_id="test-project-1",
        use_all_indexes=True
    )
    
    try:
        response = await rag_answer_service.generate_answer(test_request)
        
        print(f"✅ Answer generated successfully!")
        print(f"   📝 Response length: {len(response.response)} characters")
        print(f"   🎯 Confidence: {response.metadata.get('confidence', 'N/A')}")
        print(f"   📚 Sources: {len(response.sources)} found")
        print(f"   🔧 Method: {response.metadata.get('search_method', 'N/A')}")
        
        print(f"\n📄 Generated Answer:")
        print("-" * 40)
        print(response.response[:500] + "..." if len(response.response) > 500 else response.response)
        print("-" * 40)
        
        if response.sources:
            print(f"\n📚 Sources:")
            for source in response.sources[:3]:
                print(f"   📋 {source['fileName']} (Page {source['pageNumber']}) - {source['relevance']}% relevant")
        
    except Exception as e:
        print(f"❌ Error generating answer: {e}")
    
    # Test 4: Configuration check
    print("\n⚙️  Configuration Summary:")
    print(f"   🔗 Qdrant URL: {rag_answer_service.qdrant_url or 'Not configured'}")
    print(f"   🔗 Azure Endpoint: {rag_answer_service.azure_endpoint or 'Not configured'}")
    print(f"   📊 Collection: {rag_answer_service.collection_name}")
    print(f"   🎯 Max chunks: {rag_answer_service.max_context_chunks}")
    print(f"   📏 Min similarity: {rag_answer_service.min_similarity_score}")
    
    print("\n" + "=" * 60)
    print("✅ RAG System Test Completed!")
    
    if not rag_answer_service.qdrant_client:
        print("\n⚠️  To enable full RAG functionality:")
        print("   1. Set QDRANT_URL and QDRANT_API_KEY environment variables")
        print("   2. Upload documents to RFP_AI_Collection in Qdrant")
        print("   3. Restart the backend server")
    
    if not rag_answer_service.openai_client:
        print("\n⚠️  To enable Azure OpenAI:")
        print("   1. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY")
        print("   2. Restart the backend server")

async def main():
    """Run all RAG tests."""
    await test_rag_system()

if __name__ == "__main__":
    asyncio.run(main())