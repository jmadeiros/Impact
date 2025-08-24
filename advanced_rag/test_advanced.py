"""
Comprehensive testing suite for advanced RAG system
Tests each component step by step
"""
import os
import sys
sys.path.append('..')

def test_step_1_embeddings():
    """Test Step 1: Embedding generation"""
    print("🧪 STEP 1: Testing Embeddings")
    print("=" * 40)
    
    try:
        from embeddings_test import EmbeddingTester
        tester = EmbeddingTester()
        success = tester.run_all_tests()
        return success
    except Exception as e:
        print(f"❌ Step 1 failed: {str(e)}")
        return False

def test_step_2_vector_store():
    """Test Step 2: Vector store setup"""
    print("\n🧪 STEP 2: Testing Vector Store")
    print("=" * 40)
    
    try:
        from vector_store import VectorStoreManager
        manager = VectorStoreManager()
        
        # Check if vector store exists and has data
        count = manager.collection.count()
        if count == 0:
            print("📥 Vector store empty, populating...")
            manager.populate_vector_store()
        else:
            print(f"✅ Vector store has {count} documents")
            
        # Test search
        results = manager.search_similar("confidence building", n_results=3)
        if results:
            print(f"✅ Search test passed - found {len(results)} results")
            return True
        else:
            print("❌ Search test failed - no results")
            return False
            
    except Exception as e:
        print(f"❌ Step 2 failed: {str(e)}")
        return False

def test_step_3_langchain_rag():
    """Test Step 3: Langchain RAG system"""
    print("\n🧪 STEP 3: Testing Langchain RAG")
    print("=" * 40)
    
    try:
        from langchain_rag import AdvancedRAGSystem
        
        # Initialize system
        rag = AdvancedRAGSystem()
        
        # Test simple query
        test_query = "How do programs help young people build confidence?"
        result = rag.query(test_query)
        
        if result['evidence_count'] > 0 and len(result['answer']) > 50:
            print(f"✅ RAG test passed")
            print(f"   Evidence: {result['evidence_count']} documents")
            print(f"   Answer: {len(result['answer'])} characters")
            return True
        else:
            print("❌ RAG test failed - insufficient results")
            return False
            
    except Exception as e:
        print(f"❌ Step 3 failed: {str(e)}")
        return False

def test_step_4_comparison():
    """Test Step 4: Compare with simple system"""
    print("\n🧪 STEP 4: Testing System Comparison")
    print("=" * 40)
    
    try:
        from langchain_rag import AdvancedRAGSystem
        
        rag = AdvancedRAGSystem()
        comparison = rag.compare_with_simple_system("How do programs build confidence?")
        
        if comparison:
            print("✅ Comparison test passed")
            return True
        else:
            print("❌ Comparison test failed")
            return False
            
    except Exception as e:
        print(f"❌ Step 4 failed: {str(e)}")
        return False

def run_installation_check():
    """Check if all required packages are installed"""
    print("🔍 INSTALLATION CHECK")
    print("=" * 30)
    
    required_packages = [
        'sentence_transformers',
        'chromadb',
        'langchain',
        'langchain_google_genai',
        'langchain_community',
        'google.generativeai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install -r requirements_advanced.txt")
        return False
    
    return True

def run_environment_check():
    """Check environment variables"""
    print("\n🔍 ENVIRONMENT CHECK")
    print("=" * 30)
    
    required_vars = ['GOOGLE_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            print(f"❌ {var} - MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n💡 Set missing environment variables in ../.env file")
        return False
    
    return True

def main():
    """Run complete test suite"""
    print("🚀 ADVANCED RAG SYSTEM - COMPLETE TEST SUITE")
    print("=" * 60)
    
    # Pre-flight checks
    if not run_installation_check():
        print("\n❌ Installation check failed. Fix dependencies first.")
        return
    
    if not run_environment_check():
        print("\n❌ Environment check failed. Fix environment variables first.")
        return
    
    print("\n✅ Pre-flight checks passed!")
    
    # Step-by-step testing
    steps = [
        ("Embeddings", test_step_1_embeddings),
        ("Vector Store", test_step_2_vector_store),
        ("Langchain RAG", test_step_3_langchain_rag),
        ("System Comparison", test_step_4_comparison)
    ]
    
    results = {}
    
    for step_name, test_func in steps:
        print(f"\n{'='*60}")
        success = test_func()
        results[step_name] = success
        
        if not success:
            print(f"\n⚠️  Step '{step_name}' failed. Fix this before proceeding.")
            break
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for step_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{step_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your advanced RAG system is ready to use!")
        print("\nNext steps:")
        print("1. Run: python langchain_rag.py")
        print("2. Or start the server: python advanced_server.py")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()