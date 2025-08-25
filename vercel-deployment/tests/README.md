# Unit Tests for Vercel RAG Deployment

This directory contains comprehensive unit tests for the Vercel RAG deployment system, covering all core components and functionality.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── requirements-test.txt       # Testing dependencies
├── test_runner.py             # Custom test runner with colored output
├── test_rag_engine.py         # Tests for ServerlessRAGEngine
├── test_vector_client.py      # Tests for vector store clients
├── test_embeddings.py         # Tests for embedding generation
├── test_conversation.py       # Tests for conversational components
└── README.md                  # This file
```

## Test Coverage

### Core Components Tested

1. **RAG Engine (`test_rag_engine.py`)**
   - Serverless RAG engine initialization and configuration
   - Lazy loading of components (LLM, embeddings, vector client)
   - Query processing pipeline
   - Error handling and timeout management
   - Health checks and statistics
   - Environment variable validation

2. **Vector Clients (`test_vector_client.py`)**
   - Pinecone vector store client
   - Supabase vector store client (with pgvector)
   - Vector store factory pattern
   - Search functionality with filters
   - Document upsert and deletion
   - Health checks and statistics
   - Utility functions (similarity calculation, batching)

3. **Embeddings (`test_embeddings.py`)**
   - Serverless embedding client
   - Single and batch embedding generation
   - Request-level caching with LRU eviction
   - Similarity calculations
   - Performance optimizations
   - Factory functions and utilities

4. **Conversation Management (`test_conversation.py`)**
   - Conversation turns and sessions
   - Session management and expiration
   - Context-aware conversations
   - Conversational RAG adapter
   - Multi-turn conversation handling
   - Session statistics and history

### Test Features

- **Comprehensive Mocking**: All external dependencies (APIs, databases, models) are mocked
- **Error Handling**: Tests cover various error scenarios and edge cases
- **Performance**: Tests verify caching, lazy loading, and optimization features
- **Configuration**: Tests cover environment variable handling and configuration management
- **Serverless Constraints**: Tests verify timeout handling, memory management, and stateless operation

## Running Tests

### Prerequisites

Install testing dependencies:

```bash
pip install -r requirements-test.txt
```

### Running All Tests

#### Using the Custom Test Runner (Recommended)

```bash
# Run all tests with colored output
python tests/test_runner.py

# Run with verbose output
python tests/test_runner.py --verbose

# Run with coverage reporting
python tests/test_runner.py --coverage
```

#### Using unittest

```bash
# Run all tests
python -m unittest discover tests/ -v

# Run specific test file
python -m unittest tests.test_rag_engine -v
```

#### Using pytest

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=lib --cov-report=html

# Run specific test file
pytest tests/test_rag_engine.py -v

# Run tests in parallel
pytest tests/ -n auto
```

### Running Specific Test Categories

```bash
# Run specific component tests
python tests/test_runner.py --class rag
python tests/test_runner.py --class vector
python tests/test_runner.py --class embeddings
python tests/test_runner.py --class conversation

# Run specific vector store tests
python tests/test_runner.py --class pinecone
python tests/test_runner.py --class supabase
```

### Test Output

The custom test runner provides colored output with emojis:

```
🚀 Running Vercel RAG Deployment Unit Tests
============================================================
📦 Loading RAG Engine tests...
📦 Loading Vector Client tests...
📦 Loading Embeddings tests...
📦 Loading Conversation tests...

✅ test_initialization_with_config (test_rag_engine.TestServerlessRAGEngine)
✅ test_llm_initialization (test_rag_engine.TestServerlessRAGEngine)
...

============================================================
📊 Test Summary
============================================================
Total Tests: 89
✅ Passed: 89
⏱️  Time: 2.34s

✅ Overall Result: PASSED
```

## Test Configuration

### Environment Variables

Tests use mocked environment variables defined in `conftest.py`. No real API keys or external services are required.

### Fixtures

Common test fixtures are available in `conftest.py`:

- `mock_environment`: Mock environment variables
- `mock_rag_config`: Mock RAG configuration
- `mock_documents`: Sample document data
- `mock_search_results`: Sample search results
- `mock_rag_response`: Sample RAG response
- Various component mocks (LLM, embeddings, vector clients)

### Test Helpers

The `TestHelpers` class provides utility methods for common assertions:

```python
def test_example(test_helpers):
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
    test_helpers.assert_valid_embedding(embedding, expected_dim=5)
    
    response = {...}
    test_helpers.assert_valid_rag_response(response)
```

## Writing New Tests

### Test Structure

Follow this pattern for new test files:

```python
"""
Unit tests for [Component Name]
Tests [brief description of what's being tested]
"""
import unittest
from unittest.mock import Mock, patch
import os
import sys

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from your_module import YourClass

class TestYourClass(unittest.TestCase):
    """Test cases for YourClass"""
    
    def setUp(self):
        """Set up test fixtures"""
        pass
    
    def test_functionality(self):
        """Test specific functionality"""
        pass

if __name__ == '__main__':
    unittest.main()
```

### Best Practices

1. **Mock External Dependencies**: Always mock external APIs, databases, and file systems
2. **Test Error Cases**: Include tests for error scenarios and edge cases
3. **Use Descriptive Names**: Test method names should clearly describe what's being tested
4. **Test Both Success and Failure**: Cover both happy path and error conditions
5. **Verify Side Effects**: Check that methods are called with correct parameters
6. **Use Fixtures**: Leverage pytest fixtures for common test data
7. **Keep Tests Independent**: Each test should be able to run independently

### Example Test

```python
@patch('your_module.ExternalService')
def test_process_with_external_service(self, mock_service):
    """Test processing with external service integration"""
    # Arrange
    mock_service.return_value.call_api.return_value = {"result": "success"}
    processor = YourClass()
    
    # Act
    result = processor.process("test_input")
    
    # Assert
    self.assertEqual(result["status"], "success")
    mock_service.return_value.call_api.assert_called_once_with("test_input")
```

## Continuous Integration

These tests are designed to run in CI/CD environments without external dependencies. All external services are mocked, making tests fast and reliable.

### GitHub Actions Example

```yaml
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements-test.txt
    - name: Run tests
      run: python tests/test_runner.py --coverage
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the lib directory is in the Python path
2. **Mock Issues**: Verify that external dependencies are properly mocked
3. **Test Isolation**: Make sure tests don't depend on each other's state
4. **Environment Variables**: Check that required environment variables are mocked

### Debug Mode

Run tests with maximum verbosity to debug issues:

```bash
python tests/test_runner.py --verbose
pytest tests/ -vvv -s
```

### Coverage Reports

Generate detailed coverage reports:

```bash
python tests/test_runner.py --coverage
pytest tests/ --cov=lib --cov-report=html --cov-report=term-missing
```

The HTML coverage report will be available in `htmlcov/index.html`.

## Contributing

When adding new functionality to the codebase:

1. Write tests for new components
2. Ensure all tests pass
3. Maintain or improve test coverage
4. Update this README if adding new test categories
5. Follow the existing test patterns and conventions