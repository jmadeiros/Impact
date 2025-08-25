"""
Search API Endpoint for Vercel Deployment
Main search functionality with semantic similarity and AI responses
"""
import json
import sys
import os
from typing import Dict, Any, List, Optional

# Add lib directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from rag_engine import ServerlessRAGEngine
from vector_client import VectorStoreFactory
from serverless_error_handler import (
    timeout_handler, memory_monitor, retry_handler, graceful_degradation,
    cold_start_optimizer, format_error_response, create_fallback_response,
    ServerlessError, ErrorType
)
from user_friendly_errors import (
    format_user_friendly_error, create_user_friendly_fallback, 
    format_validation_error, get_contextual_error_message
)

@cold_start_optimizer
@timeout_handler(timeout_seconds=25, error_message="Search request timed out")
@memory_monitor
def handler(request):
    """
    Vercel serverless function handler for search endpoint
    
    Expected request body:
    {
        "query": "How do programs build confidence?",
        "max_results": 5,
        "filters": {
            "age_group": ["13-15", "16-18"],
            "organization": ["YCUK", "Palace for Life"]
        }
    }
    """
    
    # Handle CORS for browser requests
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    # Only allow POST requests
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Method not allowed. Use POST.',
                'allowed_methods': ['POST']
            })
        }
    
    try:
        # Parse request body
        if hasattr(request, 'body'):
            body = json.loads(request.body) if isinstance(request.body, str) else request.body
        else:
            body = request.json if hasattr(request, 'json') else {}
        
        # Validate required fields
        if not body.get('query'):
            validation_response = format_validation_error(
                "query", 
                "is required and cannot be empty",
                {
                    'query': 'How do programs build confidence?',
                    'max_results': 5,
                    'filters': {'age_group': ['13-15']}
                }
            )
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(validation_response)
            }
        
        # Extract parameters
        query = body['query']
        max_results = body.get('max_results', 5)
        filters = body.get('filters', {})
        
        # Validate parameters
        if not isinstance(query, str) or len(query.strip()) == 0:
            validation_response = format_validation_error(
                "query",
                "must be a non-empty text string",
                {'query': 'How do programs build confidence in young people?'}
            )
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(validation_response)
            }
        
        if max_results > 20:  # Limit to prevent excessive processing
            max_results = 20
        
        # Process the search query with error handling
        result = process_search_query_with_fallback(query, filters, max_results)
        
        # Format response for API
        api_response = {
            'success': True,
            'query': query,
            'answer': result['answer'],
            'evidence_count': result['evidence_count'],
            'source_documents': [
                {
                    'text': doc['text'],
                    'organization': doc.get('organization', 'Unknown'),
                    'age_group': doc.get('age_group', 'Unknown'),
                    'gender': doc.get('gender', 'Unknown'),
                    'question_text': doc.get('question_text', 'Unknown'),
                    'similarity_score': doc.get('score', 0.0)
                }
                for doc in result['source_documents']
            ],
            'metadata': {
                'organizations': result['organizations'],
                'age_groups': result['age_groups'],
                'genders': result['genders'],
                'system_type': result['system_type'],
                'processing_time': result['processing_time']
            },
            'filters_applied': filters,
            'timestamp': result.get('timestamp', '')
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache'
            },
            'body': json.dumps(api_response)
        }
        
    except json.JSONDecodeError as e:
        validation_response = format_validation_error(
            "request body",
            "contains invalid JSON format",
            {
                'query': 'How do programs build confidence?',
                'max_results': 5,
                'filters': {'age_group': ['13-15']}
            }
        )
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(validation_response)
        }
        
    except ServerlessError as e:
        # Handle known serverless errors with user-friendly messages
        user_query = body.get('query', 'your question') if 'body' in locals() else 'your question'
        context = {
            'query_length': len(user_query) if isinstance(user_query, str) else 0,
            'retry_count': 0,  # Could be tracked in session
            'peak_hours': False  # Could be determined by time of day
        }
        
        user_friendly_response = format_user_friendly_error(e, context, user_query)
        status_code = 503 if e.error_type in [ErrorType.TIMEOUT, ErrorType.EXTERNAL_SERVICE] else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(user_friendly_response)
        }
        
    except Exception as e:
        # Handle unexpected errors with user-friendly messages
        print(f"Search API Error: {str(e)}")
        user_query = body.get('query', 'your question') if 'body' in locals() else 'your question'
        
        user_friendly_response = format_user_friendly_error(e, user_query=user_query)
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(user_friendly_response)
        }

@retry_handler(max_retries=2, retry_on=[ErrorType.EXTERNAL_SERVICE, ErrorType.TIMEOUT])
@graceful_degradation(fallback_response=None)
def process_search_query_with_fallback(query: str, filters: Optional[Dict[str, Any]], max_results: int) -> Dict[str, Any]:
    """Process search query with comprehensive error handling and fallback"""
    try:
        # Initialize RAG engine with timeout protection
        rag_engine = ServerlessRAGEngine()
        
        # Process the search query
        result = rag_engine.process_query(query, filters=filters)
        
        # Check if we got a valid result
        if not result or result.get('evidence_count', 0) == 0:
            # Return a helpful response even with no results
            return {
                'question': query,
                'answer': "I couldn't find any relevant survey responses for your question. Try rephrasing or asking about different aspects of the youth programs.",
                'source_documents': [],
                'evidence_count': 0,
                'organizations': [],
                'age_groups': [],
                'genders': [],
                'system_type': 'serverless_rag',
                'processing_time': 0,
                'filters_applied': filters or {},
                'timestamp': ''
            }
        
        return result
        
    except Exception as e:
        # If all retries failed, create a fallback response
        print(f"Search processing failed after retries: {str(e)}")
        
        # Determine error type for appropriate fallback
        if "timeout" in str(e).lower():
            error_type = ErrorType.TIMEOUT
        elif "memory" in str(e).lower():
            error_type = ErrorType.MEMORY_LIMIT
        elif "connection" in str(e).lower() or "api" in str(e).lower():
            error_type = ErrorType.EXTERNAL_SERVICE
        else:
            error_type = ErrorType.UNKNOWN
        
        # Return user-friendly fallback response instead of raising error
        fallback = create_user_friendly_fallback(query, error_type)
        fallback['filters_applied'] = filters or {}
        return fallback

# Alternative handler for different Vercel runtime configurations
def main(request):
    """Alternative entry point"""
    return handler(request)

# For local testing
if __name__ == "__main__":
    # Mock request for testing
    class MockRequest:
        def __init__(self, method='POST', body=None):
            self.method = method
            self.body = body or json.dumps({
                'query': 'How do programs build confidence in young people?',
                'max_results': 3
            })
    
    print("🧪 Testing Search API Endpoint")
    print("=" * 40)
    
    # Test valid request
    mock_request = MockRequest()
    response = handler(mock_request)
    
    print(f"Status Code: {response['statusCode']}")
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"Success: {body['success']}")
        print(f"Evidence Count: {body['evidence_count']}")
        print(f"Processing Time: {body['metadata']['processing_time']:.3f}s")
        print(f"Answer Preview: {body['answer'][:100]}...")
    else:
        print(f"Error: {response['body']}")
    
    # Test invalid request
    print("\n" + "=" * 40)
    print("Testing invalid request...")
    
    invalid_request = MockRequest(body=json.dumps({'invalid': 'data'}))
    invalid_response = handler(invalid_request)
    print(f"Invalid Request Status: {invalid_response['statusCode']}")
    
    print("\n✅ Search API endpoint test complete!")