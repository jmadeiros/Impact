"""
Test runner for Vercel RAG deployment unit tests
Runs all test suites and provides comprehensive reporting
"""
import unittest
import sys
import os
from io import StringIO
import time

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

# Import all test modules
from test_rag_engine import TestServerlessRAGEngine, TestUtilityFunctions as RAGUtilityTests
from test_vector_client import (
    TestPineconeVectorClient, TestSupabaseVectorClient, 
    TestVectorStoreFactory, TestUtilityFunctions as VectorUtilityTests
)
from test_embeddings import (
    TestServerlessEmbeddingClient, TestEmbeddingCache, 
    TestFactoryFunctions as EmbeddingFactoryTests
)
from test_conversation import (
    TestConversationTurn, TestConversationSession, 
    TestServerlessConversationManager, TestConversationalRAGAdapter,
    TestFactoryFunction as ConversationFactoryTests
)

# Import integration test modules
try:
    from integration.test_api_endpoints import (
        TestSearchAPIIntegration, TestChatAPIIntegration, 
        TestHealthAPIIntegration, TestStatsAPIIntegration,
        TestAPIErrorHandling, TestAPIPerformance
    )
    from integration.test_external_services import (
        TestVectorStoreIntegration, TestLLMIntegration,
        TestEmbeddingIntegration, TestEndToEndIntegration
    )
    from integration.test_serverless_constraints import (
        TestColdStartPerformance, TestMemoryOptimization,
        TestTimeoutHandling, TestConcurrencyAndStatelessness,
        TestResourceConstraints
    )
    INTEGRATION_TESTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Integration tests not available: {e}")
    INTEGRATION_TESTS_AVAILABLE = False


class ColoredTextTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        self.verbosity = verbosity
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write("✅ ")
            self.stream.writeln(self.getDescription(test))
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write("❌ ")
            self.stream.writeln(self.getDescription(test))
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write("❌ ")
            self.stream.writeln(self.getDescription(test))
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write("⏭️  ")
            self.stream.writeln(f"{self.getDescription(test)} (skipped: {reason})")


class ColoredTextTestRunner(unittest.TextTestRunner):
    """Custom test runner with colored output"""
    
    resultclass = ColoredTextTestResult
    
    def run(self, test):
        print("🚀 Running Vercel RAG Deployment Unit Tests")
        print("=" * 60)
        
        start_time = time.time()
        result = super().run(test)
        end_time = time.time()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total_tests = result.testsRun
        successes = result.success_count
        failures = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {successes}")
        if failures > 0:
            print(f"❌ Failed: {failures}")
        if errors > 0:
            print(f"💥 Errors: {errors}")
        if skipped > 0:
            print(f"⏭️  Skipped: {skipped}")
        
        print(f"⏱️  Time: {end_time - start_time:.2f}s")
        
        if failures > 0 or errors > 0:
            print(f"\n❌ Overall Result: FAILED")
            return_code = 1
        else:
            print(f"\n✅ Overall Result: PASSED")
            return_code = 0
        
        # Print detailed failure/error information
        if failures:
            print("\n" + "=" * 60)
            print("❌ FAILURES")
            print("=" * 60)
            for test, traceback in result.failures:
                print(f"\n{test}:")
                print(traceback)
        
        if errors:
            print("\n" + "=" * 60)
            print("💥 ERRORS")
            print("=" * 60)
            for test, traceback in result.errors:
                print(f"\n{test}:")
                print(traceback)
        
        return result


def create_test_suite(include_integration=False):
    """Create comprehensive test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # RAG Engine tests
    print("📦 Loading RAG Engine tests...")
    suite.addTests(loader.loadTestsFromTestCase(TestServerlessRAGEngine))
    suite.addTests(loader.loadTestsFromTestCase(RAGUtilityTests))
    
    # Vector Client tests
    print("📦 Loading Vector Client tests...")
    suite.addTests(loader.loadTestsFromTestCase(TestPineconeVectorClient))
    suite.addTests(loader.loadTestsFromTestCase(TestSupabaseVectorClient))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStoreFactory))
    suite.addTests(loader.loadTestsFromTestCase(VectorUtilityTests))
    
    # Embeddings tests
    print("📦 Loading Embeddings tests...")
    suite.addTests(loader.loadTestsFromTestCase(TestServerlessEmbeddingClient))
    suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingCache))
    suite.addTests(loader.loadTestsFromTestCase(EmbeddingFactoryTests))
    
    # Conversation tests
    print("📦 Loading Conversation tests...")
    suite.addTests(loader.loadTestsFromTestCase(TestConversationTurn))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationSession))
    suite.addTests(loader.loadTestsFromTestCase(TestServerlessConversationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationalRAGAdapter))
    suite.addTests(loader.loadTestsFromTestCase(ConversationFactoryTests))
    
    # Integration tests (if requested and available)
    if include_integration and INTEGRATION_TESTS_AVAILABLE:
        print("🔗 Loading Integration tests...")
        
        # API Integration tests
        suite.addTests(loader.loadTestsFromTestCase(TestSearchAPIIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestChatAPIIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestHealthAPIIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestStatsAPIIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestAPIErrorHandling))
        suite.addTests(loader.loadTestsFromTestCase(TestAPIPerformance))
        
        # External Service Integration tests
        suite.addTests(loader.loadTestsFromTestCase(TestVectorStoreIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestLLMIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingIntegration))
        suite.addTests(loader.loadTestsFromTestCase(TestEndToEndIntegration))
        
        # Serverless Constraint tests
        suite.addTests(loader.loadTestsFromTestCase(TestColdStartPerformance))
        suite.addTests(loader.loadTestsFromTestCase(TestMemoryOptimization))
        suite.addTests(loader.loadTestsFromTestCase(TestTimeoutHandling))
        suite.addTests(loader.loadTestsFromTestCase(TestConcurrencyAndStatelessness))
        suite.addTests(loader.loadTestsFromTestCase(TestResourceConstraints))
    
    return suite


def run_specific_test_class(test_class_name):
    """Run tests for a specific class"""
    test_classes = {
        'rag': TestServerlessRAGEngine,
        'vector': TestPineconeVectorClient,
        'embeddings': TestServerlessEmbeddingClient,
        'conversation': TestConversationalRAGAdapter,
        'pinecone': TestPineconeVectorClient,
        'supabase': TestSupabaseVectorClient,
        'factory': TestVectorStoreFactory,
        'cache': TestEmbeddingCache
    }
    
    if test_class_name.lower() in test_classes:
        suite = unittest.TestSuite()
        loader = unittest.TestLoader()
        suite.addTests(loader.loadTestsFromTestCase(test_classes[test_class_name.lower()]))
        
        runner = ColoredTextTestRunner(verbosity=2)
        return runner.run(suite)
    else:
        print(f"❌ Unknown test class: {test_class_name}")
        print(f"Available classes: {', '.join(test_classes.keys())}")
        return None


def run_tests_with_coverage(include_integration=False):
    """Run tests with coverage reporting if available"""
    try:
        import coverage
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run tests
        suite = create_test_suite(include_integration=include_integration)
        runner = ColoredTextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Stop coverage and report
        cov.stop()
        cov.save()
        
        print("\n" + "=" * 60)
        print("📈 Coverage Report")
        print("=" * 60)
        cov.report()
        
        return result
        
    except ImportError:
        print("⚠️  Coverage module not available. Install with: pip install coverage")
        return run_all_tests(include_integration=include_integration)


def run_all_tests(include_integration=False):
    """Run all tests"""
    suite = create_test_suite(include_integration=include_integration)
    runner = ColoredTextTestRunner(verbosity=2)
    return runner.run(suite)


def run_integration_tests_only():
    """Run only integration tests"""
    if not INTEGRATION_TESTS_AVAILABLE:
        print("❌ Integration tests are not available")
        return None
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    print("🔗 Loading Integration tests only...")
    
    # API Integration tests
    suite.addTests(loader.loadTestsFromTestCase(TestSearchAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestChatAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestHealthAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestStatsAPIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIPerformance))
    
    # External Service Integration tests
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStoreIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndIntegration))
    
    # Serverless Constraint tests
    suite.addTests(loader.loadTestsFromTestCase(TestColdStartPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeoutHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestConcurrencyAndStatelessness))
    suite.addTests(loader.loadTestsFromTestCase(TestResourceConstraints))
    
    runner = ColoredTextTestRunner(verbosity=2)
    return runner.run(suite)


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Vercel RAG deployment tests')
    parser.add_argument('--class', dest='test_class', help='Run specific test class')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--integration', action='store_true', help='Include integration tests')
    parser.add_argument('--integration-only', action='store_true', help='Run only integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output')
    
    args = parser.parse_args()
    
    # Set verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    # Run specific test class
    if args.test_class:
        result = run_specific_test_class(args.test_class)
        if result is None:
            sys.exit(1)
        sys.exit(0 if result.wasSuccessful() else 1)
    
    # Run only integration tests
    if args.integration_only:
        result = run_integration_tests_only()
        if result is None:
            sys.exit(1)
        sys.exit(0 if result.wasSuccessful() else 1)
    
    # Run with coverage
    if args.coverage:
        result = run_tests_with_coverage(include_integration=args.integration)
        sys.exit(0 if result.wasSuccessful() else 1)
    
    # Run all tests
    result = run_all_tests(include_integration=args.integration)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()