"""
Basic structure and import test for Vercel deployment
Tests that all modules can be imported and basic functionality works
"""
import sys
import os
import traceback

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing Module Imports")
    print("=" * 40)
    
    # Add lib to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
    
    tests = []
    
    # Test vector client imports
    try:
        from vector_client import VectorStoreClient, PineconeVectorClient, SupabaseVectorClient, VectorStoreFactory
        tests.append(("✅ Vector Client", "All classes imported successfully"))
    except Exception as e:
        tests.append(("❌ Vector Client", f"Import failed: {str(e)}"))
    
    # Test embeddings imports
    try:
        from embeddings import ServerlessEmbeddingClient, create_embedding_client
        tests.append(("✅ Embeddings", "All classes imported successfully"))
    except Exception as e:
        tests.append(("❌ Embeddings", f"Import failed: {str(e)}"))
    
    # Test RAG engine imports
    try:
        from rag_engine import ServerlessRAGEngine, create_rag_engine
        tests.append(("✅ RAG Engine", "All classes imported successfully"))
    except Exception as e:
        tests.append(("❌ RAG Engine", f"Import failed: {str(e)}"))
    
    # Test conversation imports
    try:
        from conversation import ConversationalRAGAdapter, ServerlessConversationManager
        tests.append(("✅ Conversation", "All classes imported successfully"))
    except Exception as e:
        tests.append(("❌ Conversation", f"Import failed: {str(e)}"))
    
    # Print results
    for status, message in tests:
        print(f"{status}: {message}")
    
    return all("✅" in test[0] for test in tests)

def test_api_structure():
    """Test that API endpoints have correct structure"""
    print("\n🧪 Testing API Structure")
    print("=" * 40)
    
    api_files = [
        'api/search.py',
        'api/chat.py', 
        'api/health.py',
        'api/stats.py'
    ]
    
    tests = []
    
    for api_file in api_files:
        file_path = os.path.join(os.path.dirname(__file__), api_file)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Check for required functions
                has_handler = 'def handler(' in content
                has_cors = 'Access-Control-Allow-Origin' in content
                has_error_handling = 'try:' in content and 'except' in content
                
                if has_handler and has_cors and has_error_handling:
                    tests.append(("✅", f"{api_file}: Complete structure"))
                else:
                    missing = []
                    if not has_handler: missing.append("handler function")
                    if not has_cors: missing.append("CORS headers")
                    if not has_error_handling: missing.append("error handling")
                    tests.append(("⚠️", f"{api_file}: Missing {', '.join(missing)}"))
                    
            except Exception as e:
                tests.append(("❌", f"{api_file}: Read error - {str(e)}"))
        else:
            tests.append(("❌", f"{api_file}: File not found"))
    
    # Print results
    for status, message in tests:
        print(f"{status} {message}")
    
    return all("✅" in test[0] for test in tests)

def test_mock_functionality():
    """Test basic functionality with mock data"""
    print("\n🧪 Testing Mock Functionality")
    print("=" * 40)
    
    try:
        # Add lib to path
        sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
        
        # Test embedding client creation (without actual model loading)
        print("Testing embedding client creation...")
        from embeddings import ServerlessEmbeddingClient
        
        # Create client but don't initialize model yet
        client = ServerlessEmbeddingClient()
        print("✅ Embedding client created")
        
        # Test conversation manager
        print("Testing conversation manager...")
        from conversation import ServerlessConversationManager
        
        conv_manager = ServerlessConversationManager()
        session = conv_manager.create_session("test_session")
        print(f"✅ Conversation session created: {session.session_id}")
        
        # Test vector store factory (without actual connections)
        print("Testing vector store factory...")
        from vector_client import VectorStoreFactory
        
        # Test config validation
        test_config = {
            'vector_store_type': 'pinecone',
            'pinecone_api_key': 'test_key',
            'pinecone_environment': 'test_env',
            'pinecone_index_name': 'test_index'
        }
        
        try:
            # This will fail without real credentials, but tests the factory logic
            VectorStoreFactory.create_client(test_config)
        except Exception as e:
            if 'api_key' in str(e).lower() or 'environment' in str(e).lower():
                print("✅ Vector store factory validation working (expected auth error)")
            else:
                print(f"⚠️ Unexpected error: {str(e)}")
        
        print("✅ Mock functionality tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Mock functionality test failed: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Vercel Deployment Structure Test")
    print("=" * 50)
    
    # Run tests
    imports_ok = test_imports()
    structure_ok = test_api_structure()
    mock_ok = test_mock_functionality()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Module Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"API Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Mock Functionality: {'✅ PASS' if mock_ok else '❌ FAIL'}")
    
    overall_pass = imports_ok and structure_ok and mock_ok
    print(f"\nOverall: {'✅ READY FOR NEXT STEPS' if overall_pass else '❌ NEEDS FIXES'}")
    
    if overall_pass:
        print("\n🎯 Next Steps:")
        print("1. Create requirements.txt and vercel.json")
        print("2. Set up environment variables")
        print("3. Migrate ChromaDB data to Pinecone")
        print("4. Deploy to Vercel for full testing")
    
    return overall_pass

if __name__ == "__main__":
    main()