# Serverless Error Handling Documentation

## Overview

The Vercel RAG deployment includes a comprehensive error handling system designed specifically for serverless environments. This system addresses common challenges like timeouts, memory limits, cold starts, and external service failures.

## Features

### 1. Error Classification

The system automatically classifies errors into specific types:

- **TIMEOUT**: Function or service timeouts
- **MEMORY_LIMIT**: Memory usage exceeding limits
- **COLD_START**: Cold start related issues
- **EXTERNAL_SERVICE**: External API/service failures
- **RATE_LIMIT**: API rate limiting issues
- **AUTHENTICATION**: API key or authentication failures
- **VALIDATION**: Input validation errors
- **UNKNOWN**: Unclassified errors

### 2. Decorators for Error Handling

#### @timeout_handler
Monitors function execution time and prevents timeouts:

```python
@timeout_handler(timeout_seconds=25, error_message="Search request timed out")
def search_function():
    # Function implementation
    pass
```

#### @memory_monitor
Monitors memory usage to prevent OOM errors:

```python
@memory_monitor
def memory_intensive_function():
    # Function implementation
    pass
```

#### @retry_handler
Implements retry logic with exponential backoff:

```python
@retry_handler(max_retries=3, retry_on=[ErrorType.EXTERNAL_SERVICE, ErrorType.TIMEOUT])
def unreliable_function():
    # Function implementation
    pass
```

#### @graceful_degradation
Provides fallback responses when services fail:

```python
@graceful_degradation(fallback_func=fallback_function)
def primary_function():
    # Function implementation
    pass
```

#### @cold_start_optimizer
Optimizes cold start performance:

```python
@cold_start_optimizer
def handler_function():
    # Function implementation
    pass
```

### 3. Configuration

The error handler loads configuration from environment variables:

```bash
# Timeout settings (seconds)
VERCEL_TIMEOUT=25
LLM_TIMEOUT=20
VECTOR_SEARCH_TIMEOUT=10
EMBEDDING_TIMEOUT=5

# Memory settings (MB and percentages)
VERCEL_MEMORY_LIMIT=1024
MEMORY_WARNING_THRESHOLD=0.8
MEMORY_CRITICAL_THRESHOLD=0.95

# Retry settings
MAX_RETRIES=3
RETRY_DELAY=1.0
EXPONENTIAL_BACKOFF=true

# Rate limiting
RATE_LIMIT_WINDOW=60
MAX_REQUESTS_PER_WINDOW=100

# Fallback settings
ENABLE_FALLBACKS=true
FALLBACK_RESPONSE_ENABLED=true

# Debug settings
DEBUG=false
INCLUDE_STACK_TRACES=false
```

## Usage Examples

### API Endpoint with Full Error Handling

```python
from serverless_error_handler import (
    timeout_handler, memory_monitor, retry_handler, graceful_degradation,
    cold_start_optimizer, format_error_response, create_fallback_response,
    ServerlessError, ErrorType
)

@cold_start_optimizer
@timeout_handler(timeout_seconds=25, error_message="API request timed out")
@memory_monitor
def api_handler(request):
    try:
        # Process request with error handling
        result = process_request_with_fallback(request)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
        
    except ServerlessError as e:
        status_code = 503 if e.error_type in [ErrorType.TIMEOUT, ErrorType.EXTERNAL_SERVICE] else 500
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(format_error_response(e))
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(format_error_response(e))
        }

@retry_handler(max_retries=2, retry_on=[ErrorType.EXTERNAL_SERVICE, ErrorType.TIMEOUT])
@graceful_degradation(fallback_response=None)
def process_request_with_fallback(request):
    # Implementation with automatic retries and fallback
    pass
```

### Custom Error Handling

```python
# Create custom ServerlessError
error = ServerlessError(
    "Custom error message",
    ErrorType.EXTERNAL_SERVICE,
    {"additional": "context"},
    retry_after=60
)

# Format for API response
response = format_error_response(error, include_details=True)

# Create fallback response
fallback = create_fallback_response("user query", ErrorType.TIMEOUT)
```

## Error Response Format

### Standard Error Response

```json
{
  "error": true,
  "error_type": "timeout",
  "message": "Request timed out",
  "timestamp": "2025-08-25T15:00:35.248901",
  "fallback_suggestions": [
    "Try reducing the complexity of your query",
    "Break down large requests into smaller ones",
    "Check if the service is experiencing high load"
  ]
}
```

### Detailed Error Response (Debug Mode)

```json
{
  "error": true,
  "error_type": "external_service",
  "message": "Vector store connection failed",
  "timestamp": "2025-08-25T15:00:35.248901",
  "details": {
    "execution_time": 15.2,
    "retry_count": 2,
    "service": "pinecone"
  },
  "retry_after": 30,
  "fallback_suggestions": [
    "Check your internet connection",
    "Verify API keys and service credentials",
    "Try again in a few moments"
  ]
}
```

### Fallback Response

```json
{
  "success": false,
  "query": "How do programs build confidence?",
  "answer": "I'm experiencing high load right now. Please try your question again in a moment.",
  "evidence_count": 0,
  "source_documents": [],
  "metadata": {
    "system_type": "fallback_response",
    "error_type": "timeout",
    "fallback": true
  },
  "timestamp": "2025-08-25T15:00:35.248901"
}
```

## Best Practices

### 1. Decorator Order

Apply decorators in the correct order for optimal functionality:

```python
@cold_start_optimizer          # Outermost - handles cold starts
@timeout_handler(25)           # Timeout protection
@memory_monitor               # Memory monitoring
@retry_handler(max_retries=2) # Retry logic
@graceful_degradation()       # Fallback handling
def my_function():            # Innermost - actual function
    pass
```

### 2. Error Classification

Always use appropriate error types:

```python
# Good - specific error type
raise ServerlessError("API key invalid", ErrorType.AUTHENTICATION)

# Avoid - generic error type
raise ServerlessError("Something failed", ErrorType.UNKNOWN)
```

### 3. Fallback Strategies

Implement meaningful fallbacks:

```python
def search_fallback(query, **kwargs):
    return {
        "answer": "I'm temporarily unable to search. Please try again shortly.",
        "evidence_count": 0,
        "fallback": True
    }

@graceful_degradation(fallback_func=search_fallback)
def search_function(query):
    # Primary search implementation
    pass
```

### 4. Configuration Management

Use environment variables for configuration:

```python
# Load from environment with defaults
config = {
    "timeout": int(os.getenv("FUNCTION_TIMEOUT", "25")),
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "debug": os.getenv("DEBUG", "false").lower() == "true"
}
```

## Monitoring and Debugging

### 1. Logging

The error handler provides structured logging:

```python
import logging
logger = logging.getLogger(__name__)

# Error logs include context
logger.error(f"Function {func.__name__} failed: {str(e)}")
logger.warning(f"High memory usage: {memory_percent:.1f}%")
logger.info(f"Retry attempt {attempt} for {func.__name__}")
```

### 2. Performance Metrics

Track performance metrics:

```python
# Execution time tracking
start_time = time.time()
# ... function execution ...
execution_time = time.time() - start_time

# Memory usage monitoring
memory_info = error_handler._get_memory_usage()
```

### 3. Health Checks

Implement comprehensive health checks:

```python
def health_check():
    try:
        # Test all critical components
        vector_healthy = vector_client.health_check()
        llm_healthy = test_llm_connection()
        
        return {
            "status": "healthy" if all([vector_healthy, llm_healthy]) else "unhealthy",
            "components": {
                "vector_store": "healthy" if vector_healthy else "unhealthy",
                "llm": "healthy" if llm_healthy else "unhealthy"
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## Testing

### Running Error Handling Tests

```bash
# Run comprehensive error handling tests
python3 vercel-deployment/test_error_handling.py
```

### Test Coverage

The test suite covers:

- Error classification accuracy
- Timeout handling behavior
- Retry logic with exponential backoff
- Graceful degradation mechanisms
- Memory monitoring functionality
- API response formatting
- Configuration loading
- Fallback response generation

## Troubleshooting

### Common Issues

1. **Memory Monitoring Not Available**
   - Install psutil: `pip install psutil`
   - Or accept limited memory info without psutil

2. **Timeouts Still Occurring**
   - Reduce timeout values in configuration
   - Optimize function performance
   - Implement better caching

3. **Retries Not Working**
   - Check error types in retry_on list
   - Verify retry delay configuration
   - Monitor external service status

4. **Fallbacks Not Triggering**
   - Ensure fallback functions are properly defined
   - Check graceful_degradation decorator placement
   - Verify error types match fallback conditions

### Debug Mode

Enable debug mode for detailed error information:

```bash
export DEBUG=true
export INCLUDE_STACK_TRACES=true
```

This provides:
- Full error details in responses
- Stack traces for debugging
- Additional logging information
- Performance metrics

## Integration with Vercel

### Environment Variables

Set these in your Vercel project settings:

```bash
# Required for production
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment

# Error handling configuration
VERCEL_TIMEOUT=25
MAX_RETRIES=3
MEMORY_WARNING_THRESHOLD=0.8
DEBUG=false
```

### Function Configuration

Update `vercel.json` for optimal error handling:

```json
{
  "functions": {
    "api/*.py": {
      "runtime": "python3.9",
      "maxDuration": 25,
      "memory": 1024,
      "environment": {
        "VERCEL_TIMEOUT": "25",
        "MAX_RETRIES": "3"
      }
    }
  }
}
```

This comprehensive error handling system ensures your Vercel RAG deployment is robust, reliable, and provides excellent user experience even when things go wrong.