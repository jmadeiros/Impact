#!/usr/bin/env python3
"""
Basic integration test to check external dependencies
"""
import sys
from pathlib import Path

# Add lib directory to Python path
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing module imports...")
    
    try:
        from rag_engine import ServerlessRAGEngine
        print("✅ rag_engine import successful")
    except Exception as e:
        print(f"❌ rag_engine import failed: {e}")
        return False
    
    try:
        from vector_client import PineconeVectorClient, SupabaseVectorClient
        print("✅ vector_client import successful")
    except Exception as e:
        print(f"❌ vector_client import failed: {e}")
        return False
    
    try:
        from embeddings import ServerlessEmbeddingClient
        print("✅ embeddings import successful")
    except Exception as e:
        print(f"❌ embeddings import failed: {e}")
        return False
    
    try:
        from conversation import ConversationalRAGAdapter
        print("✅ conversation import successful")
    except Exception as e:
        print(f"❌ conversation import failed: {e}")
        return False
    
    return True

def test_basic_initialization():
    """Test basic initialization without external services"""
    print("\\n🔧 Testing basic initialization...")
    
    try:
        from config import RAGConfig
        config = RAGConfig(
            google_api_key="test_key",
            vector_store_type="supabase",  # Use supabase to avoid Pinecone requirements
            supabase_url="test_url",
            supabase_key="test_key"
        )
        print("✅ RAGConfig initialization successful")
    except Exception as e:
        print(f"❌ RAGConfig initialization failed: {e}")
        return False
    
    try:
        from embeddings import EmbeddingCache
        cache = EmbeddingCache(max_size=100)
        print("✅ EmbeddingCache initialization successful")
    except Exception as e:
        print(f"❌ EmbeddingCache initialization failed: {e}")
        return False
    
    try:
        from conversation import ServerlessConversationManager
        manager = ServerlessConversationManager()
        print("✅ ConversationManager initialization successful")
    except Exception as e:
        print(f"❌ ConversationManager initialization failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 Basic Integration Test for Vercel RAG Deployment")
    print("=" * 60)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic initialization
    if not test_basic_initialization():
        success = False
    
    print("\\n" + "=" * 60)
    if success:
        print("✅ All basic integration tests passed!")
        print("💡 Core system is ready for deployment")
    else:
        print("❌ Some integration tests failed")
        print("💡 Check dependencies and configuration")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)