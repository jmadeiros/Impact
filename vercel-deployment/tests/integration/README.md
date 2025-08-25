# Integration Tests for Vercel RAG Deployment

This directory contains comprehensive integration tests that verify the end-to-end functionality of the Vercel RAG deployment system, including API endpoints, external service integration, and serverless constraints.

## Test Structure

```
tests/integration/
├── __init__.py                           # Integration tests package
├── test_api_endpoints.py                 # API endpoint integration tests
├── test_external_services.py             # External service integration tests
├── test_serverless_constraints.py        # Serverless optimization tests
└── README.md                            # This file
```

## Test Categories

### 1. API Endpoint Integration (`test_api_endpoints.py`)

Tests the complete API functionality with realistic request/response cycles:

#### Search API Integration
- **TestSearchAPIIntegration**: End-to-end search functionality
  - Successful search requests with filters
  - Validation error handling
  - RAG engine error propagation
  - HTTP method validation
  - Response format verification

#### Chat API Integration
- **TestChatAPIIntegration**: Conversational interface testing
  - Multi-turn conversations
  - Session management
  - Context handling
  - Default parameter behavior

#### Health API Integration
- **TestHealthAPIIntegration**: System health monitoring
  - Basic health checks
  - Detailed system information
  - Component status reporting
  - Unhealthy state handling

#### Stats API Integration
- **TestStatsAPIIntegration**: System statistics and metrics
  - Performance metrics
  - Usage statistics
  - Configuration reporting

#### Error Handling Integration
- **TestAPIErrorHandling**: Comprehensive error scenarios
  - Invalid JSON handling
  - Missing headers
  - Environment variable failures
  - Graceful degradation

#### Performance Integration
- **TestAPIPerformance**: Performance characteristics
  - Response time validation
  - Concurrent request simulation
  - Load testing scenarios

### 2. External Service Integration (`test_external_services.py`)

Tests integration with external services and complete system workflows:

#### Vector Store Integration
- **TestVectorStoreIntegration**: Complete vector store workflows
  - Pinecone integration (upsert, search, delete, health, stats)
  - Supabase integration with pgvector
  - Factory pattern testing
  - Error handling and fallback behavior

#### LLM Integration
- **TestLLMIntegration**: Language model integration
  - Google Gemini LLM integration
  - Response generation
  - Error handling and rate limiting
  - Prompt formatting and context handling

#### Embedding Integration
- **TestEmbeddingIntegration**: Embedding service integration
  - SentenceTransformer integration
  - Batch processing optimization
  - Caching behavior validation
  - Performance optimization testing

#### End-to-End Integration
- **TestEndToEndIntegration**: Complete system integration
  - Full RAG pipeline testing
  - Conversational RAG integration
  - Error propagation through pipeline
  - Performance under simulated load

### 3. Serverless Constraints (`test_serverless_constraints.py`)

Tests serverless-specific optimizations and constraints:

#### Cold Start Performance
- **TestColdStartPerformance**: Initialization optimization
  - Lazy loading validation
  - Component initialization timing
  - Memory usage during startup
  - First-request performance

#### Memory Optimization
- **TestMemoryOptimization**: Memory usage management
  - Cache size limits
  - Session memory management
  - Stateless operation verification
  - Memory leak prevention

#### Timeout Handling
- **TestTimeoutHandling**: Time constraint management
  - Query processing timeouts
  - Component timeout handling
  - Session expiration
  - Performance within limits

#### Concurrency and Statelessness
- **TestConcurrencyAndStatelessness**: Concurrent operation
  - Multiple simultaneous requests
  - Session isolation
  - State independence
  - Thread safety

#### Resource Constraints
- **TestResourceConstraints**: Resource limitation handling
  - Large batch processing
  - Memory-efficient operations
  - Error recovery
  - Graceful degradation

## Running Integration Tests

### Prerequisites

Integration tests require the same dependencies as unit tests:

```bash
pip install -r tests/requirements-test.txt
```

### Running All Integration Tests

```bash
# Run only integration tests
python tests/test_runner.py --integration-only

# Run unit tests + integration tests
python tests/test_runner.py --integration

# Run with coverage
python tests/test_runner.py --integration --coverage
```

### Running Specific Integration Test Categories

```bash
# Run specific integration test file
python -m unittest tests.integration.test_api_endpoints -v
python -m unittest tests.integration.test_external_services -v
python -m unittest tests.integration.test_serverless_constraints -v

# Run specific test class
python -m unittest tests.integration.test_api_endpoints.TestSearchAPIIntegration -v
```

### Using pytest

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with markers
pytest tests/integration/ -m integration -v

# Run specific test file
pytest tests/integration/test_api_endpoints.py -v
```

## Test Configuration

### Mocking Strategy

Integration tests use comprehensive mocking to simulate external services:

- **API Tests**: Mock RAG engine and components while testing API layer
- **Service Tests**: Mock external APIs (Pinecone, Google AI) while testing integration logic
- **Constraint Tests**: Mock components with realistic delays and resource usage

### Environment Setup

Tests automatically set up mock environment variables:

```python
@patch.dict(os.environ, {
    "GOOGLE_API_KEY": "test_key",
    "PINECONE_API_KEY": "test_key",
    "PINECONE_ENVIRONMENT": "test_env",
    "PINECONE_INDEX_NAME": "test_index"
})
```

### Performance Benchmarks

Integration tests include performance benchmarks:

- **API Response Time**: < 10 seconds for mocked components
- **Cold Start**: < 2 seconds for component initialization
- **Memory Usage**: Reasonable cache sizes and session limits
- **Concurrent Processing**: Multiple requests without interference

## Test Data

### Mock Documents

```python
mock_documents = [
    {
        "id": "doc1",
        "text": "Programs help build confidence through structured activities.",
        "embedding": [0.1, 0.2, 0.3, ...],
        "charity_name": "YCUK",
        "age_group": "16-18",
        "gender": "Female",
        "question_text": "How do programs help?",
        "created_at": "2024-01-01T10:00:00Z"
    }
]
```

### Mock API Requests

```python
search_request = {
    "query": "How do programs build confidence in young people?",
    "max_results": 5,
    "filters": {
        "age_group": ["16-18"],
        "organization": ["YCUK"]
    }
}

chat_request = {
    "message": "How do programs build confidence?",
    "session_id": "test_session_123",
    "include_context": True
}
```

## Expected Outcomes

### Success Criteria

Integration tests verify:

1. **API Functionality**: All endpoints respond correctly with proper status codes
2. **Data Flow**: Information flows correctly through the entire system
3. **Error Handling**: Errors are caught and handled gracefully at all levels
4. **Performance**: System meets performance requirements under load
5. **Serverless Compatibility**: System works within serverless constraints

### Performance Targets

- **API Response Time**: < 10 seconds (with mocked external services)
- **Cold Start Time**: < 2 seconds for component initialization
- **Memory Usage**: Reasonable limits for caching and sessions
- **Concurrent Requests**: Handle multiple simultaneous requests

### Error Scenarios

Tests cover various error conditions:

- Network failures to external services
- Invalid input data and malformed requests
- Resource exhaustion and timeout scenarios
- Configuration errors and missing environment variables

## Debugging Integration Tests

### Verbose Output

```bash
python tests/test_runner.py --integration-only --verbose
```

### Individual Test Debugging

```bash
# Run single test with maximum verbosity
python -m unittest tests.integration.test_api_endpoints.TestSearchAPIIntegration.test_search_endpoint_success -v
```

### Mock Inspection

Integration tests include detailed mock verification:

```python
# Verify external service calls
mock_vector_client.search.assert_called_once_with(
    query_embedding=[0.1, 0.2, 0.3],
    top_k=5,
    filters={"age_group": ["16-18"]}
)

# Verify response structure
self.assertEqual(response['statusCode'], 200)
self.assertIn('answer', response_body)
```

## Continuous Integration

Integration tests are designed for CI/CD environments:

### GitHub Actions Example

```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-test:
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
    - name: Run integration tests
      run: python tests/test_runner.py --integration-only --coverage
```

### Test Isolation

- No external API calls (all mocked)
- No persistent state between tests
- Independent test execution
- Deterministic results

## Contributing

When adding new integration tests:

1. **Follow Existing Patterns**: Use the same mocking and assertion patterns
2. **Test Real Scenarios**: Focus on realistic usage patterns
3. **Include Error Cases**: Test both success and failure scenarios
4. **Performance Awareness**: Include timing and resource usage checks
5. **Documentation**: Update this README with new test categories

### Adding New API Tests

```python
class TestNewAPIIntegration(unittest.TestCase):
    """Integration tests for new API endpoint"""
    
    @patch.dict(os.environ, {...})
    @patch('module.ExternalService')
    def test_new_endpoint_success(self, mock_service):
        """Test successful new endpoint request"""
        # Setup mocks
        mock_service.return_value = expected_response
        
        # Test endpoint
        response = handler(test_event, {})
        
        # Verify results
        self.assertEqual(response['statusCode'], 200)
        # ... additional assertions
```

This comprehensive integration test suite ensures that the Vercel RAG deployment works correctly as a complete system, handling real-world scenarios and constraints effectively.