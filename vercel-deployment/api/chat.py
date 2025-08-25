"""
Chat API Endpoint for Vercel Deployment
Conversational interface with session management and context awareness
"""
import json
import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add lib directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from rag_engine import ServerlessRAGEngine
from conversation import ConversationalRAGAdapter, ServerlessConversationManager
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
@timeout_handler(timeout_seconds=25, error_message="Chat request timed out")
@memory_monitor
def handler(request):
    """
    Vercel serverless function handler for chat endpoint
    
    Expected request body:
    {
        "message": "How do programs build confidence?",
        "session_id": "user_123",
        "include_context": true,
        "max_results": 5
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
        if not body.get('message'):
            validation_response = format_validation_error(
                "message",
                "is required for chat conversations",
                {
                    'message': 'How do programs build confidence?',
                    'session_id': 'user_123',
                    'include_context': True
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
        message = body['message']
        session_id = body.get('session_id', 'default')
        include_context = body.get('include_context', True)
        max_results = body.get('max_results', 5)
        
        # Validate parameters
        if not isinstance(message, str) or len(message.strip()) == 0:
            validation_response = format_validation_error(
                "message",
                "must be a non-empty text message",
                {'message': 'How do programs build confidence in young people?'}
            )
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(validation_response)
            }
        
        if len(message) > 1000:  # Limit message length
            validation_response = format_validation_error(
                "message",
                f"is too long ({len(message)} characters). Please keep messages under 1000 characters",
                {'message': 'How do programs build confidence? (shorter version)'}
            )
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(validation_response)
            }
        
        # Process the chat message with error handling
        result = process_chat_message_with_fallback(
            message, session_id, include_context, max_results
        )
        
        # Format response for API
        api_response = {
            'success': True,
            'message': result['answer'],
            'evidence_count': result['evidence_count'],
            'source_documents': [
                {
                    'text': doc.get('text', ''),
                    'organization': doc.get('organization', 'Unknown'),
                    'age_group': doc.get('age_group', 'Unknown'),
                    'gender': doc.get('gender', 'Unknown'),
                    'question_text': doc.get('question_text', 'Unknown'),
                    'similarity_score': doc.get('score', 0.0)
                }
                for doc in result.get('source_documents', [])
            ],
            'metadata': {
                'organizations': result.get('organizations', []),
                'age_groups': result.get('age_groups', []),
                'genders': result.get('genders', []),
                'session_id': result.get('session_id', session_id),
                'turn_number': result.get('turn_number', 1),
                'conversation_context_used': result.get('conversation_context_used', False),
                'processing_time': result.get('total_processing_time', 0),
                'system_type': result.get('system_type', 'conversational_rag')
            },
            'conversation': {
                'session_id': session_id,
                'turn_number': result.get('turn_number', 1),
                'context_used': result.get('conversation_context_used', False),
                'is_follow_up': result.get('turn_number', 1) > 1
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Add conversation metadata if available
        if 'conversation_metadata' in result:
            api_response['conversation'].update(result['conversation_metadata'])
        
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
                'message': 'How do programs build confidence?',
                'session_id': 'user_123',
                'include_context': True
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
        user_message = body.get('message', 'your message') if 'body' in locals() else 'your message'
        session_id = body.get('session_id', 'default') if 'body' in locals() else 'default'
        
        context = {
            'query_length': len(user_message) if isinstance(user_message, str) else 0,
            'session_id': session_id,
            'is_conversation': True
        }
        
        user_friendly_response = format_user_friendly_error(e, context, user_message)
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
        print(f"Chat API Error: {str(e)}")
        user_message = body.get('message', 'your message') if 'body' in locals() else 'your message'
        
        user_friendly_response = format_user_friendly_error(e, user_query=user_message)
        
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
def process_chat_message_with_fallback(message: str, session_id: str, 
                                     include_context: bool, max_results: int) -> Dict[str, Any]:
    """Process chat message with comprehensive error handling and fallback"""
    try:
        # Initialize RAG engine and conversational adapter with timeout protection
        rag_engine = ServerlessRAGEngine()
        conversation_manager = ServerlessConversationManager(
            max_turns_per_session=10,
            session_timeout_hours=24
        )
        conv_rag = ConversationalRAGAdapter(rag_engine, conversation_manager)
        
        # Process the chat message
        result = conv_rag.chat(
            message=message,
            session_id=session_id,
            include_context=include_context
        )
        
        return result
        
    except Exception as e:
        # If all retries failed, create a fallback response
        print(f"Chat processing failed after retries: {str(e)}")
        
        # Determine error type for appropriate fallback
        if "timeout" in str(e).lower():
            error_type = ErrorType.TIMEOUT
        elif "memory" in str(e).lower():
            error_type = ErrorType.MEMORY_LIMIT
        elif "connection" in str(e).lower() or "api" in str(e).lower():
            error_type = ErrorType.EXTERNAL_SERVICE
        else:
            error_type = ErrorType.UNKNOWN
        
        # Create user-friendly fallback response for chat
        fallback_response = create_user_friendly_fallback(message, error_type)
        
        # Adapt for chat format
        return {
            'answer': fallback_response['answer'],
            'evidence_count': 0,
            'source_documents': [],
            'organizations': [],
            'age_groups': [],
            'genders': [],
            'session_id': session_id,
            'turn_number': 1,
            'conversation_context_used': False,
            'total_processing_time': 0,
            'system_type': 'user_friendly_fallback_chat',
            'error_type': error_type.value,
            'fallback': True,
            'user_friendly': True,
            'error_info': fallback_response.get('error_info', {})
        }

# GET endpoint for retrieving conversation history
def get_conversation_history(request, session_id: str):
    """Get conversation history for a session"""
    try:
        # Initialize conversation manager
        rag_engine = ServerlessRAGEngine()
        conversation_manager = ServerlessConversationManager()
        conv_rag = ConversationalRAGAdapter(rag_engine, conversation_manager)
        
        # Get conversation history
        history = conv_rag.get_conversation_history(session_id, max_turns=20)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'session_id': session_id,
                'history': history,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve conversation history',
                'session_id': session_id,
                'details': str(e) if os.getenv('DEBUG') == 'true' else None
            })
        }

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
                'message': 'How do programs build confidence in young people?',
                'session_id': 'test_session_123',
                'include_context': True
            })
    
    print("🧪 Testing Chat API Endpoint")
    print("=" * 40)
    
    # Test first message
    mock_request = MockRequest()
    response = handler(mock_request)
    
    print(f"Status Code: {response['statusCode']}")
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"Success: {body['success']}")
        print(f"Turn Number: {body['conversation']['turn_number']}")
        print(f"Evidence Count: {body['evidence_count']}")
        print(f"Context Used: {body['conversation']['context_used']}")
        print(f"Message Preview: {body['message'][:100]}...")
    else:
        print(f"Error: {response['body']}")
    
    # Test follow-up message
    print("\n" + "=" * 40)
    print("Testing follow-up message...")
    
    followup_request = MockRequest(body=json.dumps({
        'message': 'What about social connections?',
        'session_id': 'test_session_123',
        'include_context': True
    }))
    
    followup_response = handler(followup_request)
    if followup_response['statusCode'] == 200:
        followup_body = json.loads(followup_response['body'])
        print(f"Follow-up Turn: {followup_body['conversation']['turn_number']}")
        print(f"Is Follow-up: {followup_body['conversation']['is_follow_up']}")
    
    # Test invalid request
    print("\n" + "=" * 40)
    print("Testing invalid request...")
    
    invalid_request = MockRequest(body=json.dumps({'invalid': 'data'}))
    invalid_response = handler(invalid_request)
    print(f"Invalid Request Status: {invalid_response['statusCode']}")
    
    print("\n✅ Chat API endpoint test complete!")