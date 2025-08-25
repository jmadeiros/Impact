"""
Stats and Monitoring API Endpoint for Vercel Deployment
System statistics, performance metrics, and usage tracking
"""
import json
import sys
import os
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Add lib directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from rag_engine import ServerlessRAGEngine
from vector_client import VectorStoreFactory
from conversation import ServerlessConversationManager, ConversationalRAGAdapter

def handler(request):
    """
    Vercel serverless function handler for stats endpoint
    
    GET /api/stats - Basic system statistics
    GET /api/stats?type=vector - Vector store statistics
    GET /api/stats?type=conversations - Conversation statistics
    GET /api/stats?type=performance - Performance metrics
    """
    
    # Handle CORS for browser requests
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    # Only allow GET requests
    if request.method != 'GET':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Method not allowed. Use GET.',
                'allowed_methods': ['GET']
            })
        }
    
    try:
        start_time = time.time()
        
        # Parse query parameters
        query_params = getattr(request, 'args', {}) or {}
        stats_type = query_params.get('type', 'basic').lower()
        
        # Generate appropriate statistics based on type
        if stats_type == 'vector':
            stats_response = get_vector_store_stats()
        elif stats_type == 'conversations':
            stats_response = get_conversation_stats()
        elif stats_type == 'performance':
            stats_response = get_performance_stats()
        elif stats_type == 'system':
            stats_response = get_system_stats()
        else:
            stats_response = get_basic_stats()
        
        # Add common metadata
        stats_response.update({
            'timestamp': datetime.now().isoformat(),
            'stats_type': stats_type,
            'response_time': time.time() - start_time,
            'environment': os.getenv('VERCEL_ENV', 'development'),
            'region': os.getenv('VERCEL_REGION', 'unknown')
        })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'public, max-age=60'  # Cache for 1 minute
            },
            'body': json.dumps(stats_response)
        }
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Stats API Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Failed to retrieve statistics',
                'stats_type': query_params.get('type', 'basic'),
                'details': str(e) if os.getenv('DEBUG') == 'true' else 'Enable DEBUG mode for details',
                'timestamp': datetime.now().isoformat()
            })
        }

def get_basic_stats() -> Dict[str, Any]:
    """Get basic system statistics"""
    try:
        # Initialize components
        rag_engine = ServerlessRAGEngine()
        
        # Get basic stats
        rag_stats = rag_engine.get_stats()
        
        return {
            'service': 'Advanced RAG System',
            'version': '1.0.0',
            'status': 'operational',
            'system_type': rag_stats.get('system_type', 'serverless_rag'),
            'configuration': {
                'llm_model': rag_stats.get('config', {}).get('llm_model', 'unknown'),
                'embedding_model': rag_stats.get('config', {}).get('embedding_model', 'unknown'),
                'vector_store_type': rag_stats.get('vector_store', {}).get('vector_store_type', 'unknown'),
                'max_results': rag_stats.get('config', {}).get('max_results', 5)
            },
            'capabilities': [
                'Semantic search',
                'Conversational AI',
                'Evidence-based responses',
                'Multi-turn conversations',
                'Survey data analysis'
            ]
        }
        
    except Exception as e:
        return {
            'error': f'Failed to get basic stats: {str(e)}',
            'service': 'Advanced RAG System',
            'status': 'error'
        }

def get_vector_store_stats() -> Dict[str, Any]:
    """Get vector store statistics"""
    try:
        # Initialize vector store client
        vector_client = VectorStoreFactory.create_from_env()
        vector_stats = vector_client.get_stats()
        
        # Enhanced vector store information
        enhanced_stats = {
            'vector_store': vector_stats,
            'data_overview': {
                'total_documents': vector_stats.get('total_vectors', 0),
                'organizations': ['YCUK', 'I AM IN ME', 'Palace for Life', 'Symphony Studios'],  # From your system
                'age_groups': ['12-14', '15-17'],  # From your system
                'question_types': ['MCQ', 'Rating', 'Story'],  # From your system
                'data_source': 'Youth program survey responses'
            },
            'search_capabilities': {
                'semantic_similarity': True,
                'metadata_filtering': True,
                'cross_organization_search': True,
                'demographic_analysis': True
            }
        }
        
        # Add performance metrics if available
        if 'index_fullness' in vector_stats:
            enhanced_stats['performance'] = {
                'index_fullness': vector_stats['index_fullness'],
                'estimated_query_time': '< 100ms' if vector_stats.get('vector_store_type') == 'pinecone' else '< 500ms'
            }
        
        return enhanced_stats
        
    except Exception as e:
        return {
            'error': f'Failed to get vector store stats: {str(e)}',
            'vector_store': {'status': 'error'}
        }

def get_conversation_stats() -> Dict[str, Any]:
    """Get conversation statistics"""
    try:
        # Initialize conversation components
        rag_engine = ServerlessRAGEngine()
        conversation_manager = ServerlessConversationManager()
        conv_rag = ConversationalRAGAdapter(rag_engine, conversation_manager)
        
        # Get conversation statistics
        session_stats = conv_rag.get_all_sessions_stats()
        
        # Enhanced conversation information
        enhanced_stats = {
            'conversations': session_stats,
            'features': {
                'multi_turn_support': True,
                'context_awareness': True,
                'session_management': True,
                'conversation_history': True,
                'max_turns_per_session': 10,
                'session_timeout_hours': 24
            },
            'usage_patterns': {
                'average_turns_per_session': (
                    session_stats['total_turns'] / max(1, session_stats['active_sessions'])
                    if session_stats['active_sessions'] > 0 else 0
                ),
                'active_sessions': session_stats['active_sessions'],
                'total_conversation_turns': session_stats['total_turns']
            }
        }
        
        return enhanced_stats
        
    except Exception as e:
        return {
            'error': f'Failed to get conversation stats: {str(e)}',
            'conversations': {'active_sessions': 0, 'total_turns': 0}
        }

def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics"""
    try:
        # System performance metrics
        performance_stats = {
            'serverless_metrics': {
                'cold_start': os.getenv('VERCEL_COLD_START') == '1',
                'function_region': os.getenv('VERCEL_REGION', 'unknown'),
                'deployment_id': os.getenv('VERCEL_DEPLOYMENT_ID', 'unknown')
            },
            'processing_benchmarks': {
                'typical_query_time': '2-5 seconds',
                'embedding_generation': '< 1 second',
                'vector_search': '< 100ms (Pinecone) / < 500ms (Supabase)',
                'llm_response': '1-3 seconds',
                'total_pipeline': '2-5 seconds'
            },
            'optimization_features': {
                'request_level_caching': True,
                'lazy_component_loading': True,
                'batch_embedding_processing': True,
                'memory_efficient_conversations': True
            },
            'resource_usage': get_resource_usage()
        }
        
        return performance_stats
        
    except Exception as e:
        return {
            'error': f'Failed to get performance stats: {str(e)}',
            'performance': {'status': 'error'}
        }

def get_system_stats() -> Dict[str, Any]:
    """Get comprehensive system statistics"""
    try:
        # Combine all stats
        basic = get_basic_stats()
        vector = get_vector_store_stats()
        conversations = get_conversation_stats()
        performance = get_performance_stats()
        
        return {
            'overview': basic,
            'vector_store': vector.get('vector_store', {}),
            'conversations': conversations.get('conversations', {}),
            'performance': performance.get('serverless_metrics', {}),
            'data_summary': {
                'survey_responses': vector.get('data_overview', {}).get('total_documents', 0),
                'organizations': 4,  # YCUK, I AM IN ME, Palace for Life, Symphony Studios
                'age_groups': 2,     # 12-14, 15-17
                'active_conversations': conversations.get('conversations', {}).get('active_sessions', 0)
            },
            'api_endpoints': {
                'search': '/api/search',
                'chat': '/api/chat',
                'health': '/api/health',
                'stats': '/api/stats'
            }
        }
        
    except Exception as e:
        return {
            'error': f'Failed to get system stats: {str(e)}',
            'system': {'status': 'error'}
        }

def get_resource_usage() -> Dict[str, Any]:
    """Get current resource usage"""
    try:
        import psutil
        process = psutil.Process()
        
        return {
            'memory': {
                'rss_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2)
            },
            'cpu': {
                'percent': round(process.cpu_percent(), 2)
            },
            'limits': {
                'vercel_memory_limit_mb': 1024,
                'vercel_timeout_seconds': int(os.getenv('VERCEL_TIMEOUT', '10'))
            }
        }
    except ImportError:
        return {
            'memory': {'note': 'psutil not available'},
            'limits': {
                'vercel_memory_limit_mb': 1024,
                'vercel_timeout_seconds': int(os.getenv('VERCEL_TIMEOUT', '10'))
            }
        }
    except Exception as e:
        return {'error': f'Resource usage unavailable: {str(e)}'}

# Alternative handler for different Vercel runtime configurations
def main(request):
    """Alternative entry point"""
    return handler(request)

# For local testing
if __name__ == "__main__":
    # Mock request for testing
    class MockRequest:
        def __init__(self, method='GET', args=None):
            self.method = method
            self.args = args or {}
    
    print("🧪 Testing Stats API Endpoint")
    print("=" * 40)
    
    # Test basic stats
    mock_request = MockRequest()
    response = handler(mock_request)
    
    print(f"Basic Stats Status: {response['statusCode']}")
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"Service: {body.get('service', 'Unknown')}")
        print(f"Stats Type: {body.get('stats_type', 'Unknown')}")
        print(f"Response Time: {body.get('response_time', 0):.3f}s")
    
    # Test vector stats
    print("\n" + "=" * 40)
    print("Testing vector store stats...")
    
    vector_request = MockRequest(args={'type': 'vector'})
    vector_response = handler(vector_request)
    
    if vector_response['statusCode'] == 200:
        vector_body = json.loads(vector_response['body'])
        print(f"Vector Store Type: {vector_body.get('vector_store', {}).get('vector_store_type', 'Unknown')}")
        print(f"Total Documents: {vector_body.get('data_overview', {}).get('total_documents', 0)}")
    
    # Test conversation stats
    print("\n" + "=" * 40)
    print("Testing conversation stats...")
    
    conv_request = MockRequest(args={'type': 'conversations'})
    conv_response = handler(conv_request)
    
    if conv_response['statusCode'] == 200:
        conv_body = json.loads(conv_response['body'])
        print(f"Active Sessions: {conv_body.get('conversations', {}).get('active_sessions', 0)}")
    
    # Test system stats
    print("\n" + "=" * 40)
    print("Testing system stats...")
    
    system_request = MockRequest(args={'type': 'system'})
    system_response = handler(system_request)
    
    if system_response['statusCode'] == 200:
        system_body = json.loads(system_response['body'])
        print(f"API Endpoints: {list(system_body.get('api_endpoints', {}).keys())}")
    
    print("\n✅ Stats API endpoint test complete!")