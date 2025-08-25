#!/usr/bin/env python3
"""
Core test runner for Vercel RAG deployment
Runs tests that don't require external services
"""
import unittest
import sys
import os
from pathlib import Path

# Add lib directory to Python path
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

# Add tests directory to Python path
tests_path = Path(__file__).parent / "tests"
sys.path.insert(0, str(tests_path))

def run_core_tests():
    """Run core tests that don't require external services"""
    print("🚀 Running Core Vercel RAG Deployment Tests")
    print("=" * 60)
    
    # Test classes that don't require external services
    core_test_classes = [
        # Embeddings tests (cache functionality)
        ('test_embeddings', 'TestEmbeddingCache'),
        
        # Conversation tests (all should work without external deps)
        ('test_conversation', 'TestConversationTurn'),
        ('test_conversation', 'TestConversationSession'),
        ('test_conversation', 'TestServerlessConversationManager'),
        
        # Config tests (if any)
        # Add more as needed
    ]
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    for module_name, class_name in core_test_classes:
        try:
            print(f"📦 Loading {module_name}.{class_name}...")
            module = __import__(module_name)
            test_class = getattr(module, class_name)
            suite.addTests(loader.loadTestsFromTestCase(test_class))
        except Exception as e:
            print(f"⚠️  Could not load {module_name}.{class_name}: {e}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    print("📊 Core Test Summary")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {successes}")
    if failures > 0:
        print(f"❌ Failed: {failures}")
    if errors > 0:
        print(f"💥 Errors: {errors}")
    
    if failures > 0 or errors > 0:
        print(f"\\n❌ Overall Result: FAILED")
        return False
    else:
        print(f"\\n✅ Overall Result: PASSED")
        return True

def run_integration_tests():
    """Run integration tests that require external services"""
    print("🌐 Running Integration Tests (requires external services)")
    print("=" * 60)
    
    # These tests require external services to be configured
    integration_test_classes = [
        ('test_rag_engine', 'TestServerlessRAGEngine'),
        ('test_vector_client', 'TestPineconeVectorClient'),
        ('test_vector_client', 'TestSupabaseVectorClient'),
        ('test_embeddings', 'TestServerlessEmbeddingClient'),
        ('test_conversation', 'TestConversationalRAGAdapter'),
    ]
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    for module_name, class_name in integration_test_classes:
        try:
            print(f"📦 Loading {module_name}.{class_name}...")
            module = __import__(module_name)
            test_class = getattr(module, class_name)
            suite.addTests(loader.loadTestsFromTestCase(test_class))
        except Exception as e:
            print(f"⚠️  Could not load {module_name}.{class_name}: {e}")
    
    if suite.countTestCases() == 0:
        print("⚠️  No integration tests could be loaded")
        return False
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Vercel RAG deployment tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests (requires external services)')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    success = True
    
    if args.all:
        print("Running both core and integration tests...")
        success = run_core_tests()
        if success:
            success = run_integration_tests()
    elif args.integration:
        success = run_integration_tests()
    else:
        success = run_core_tests()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()