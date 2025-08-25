"""
Health Check API Endpoint for Vercel Deployment
System status monitoring and readiness checks
"""
import json
import sys
import os
import time
from typing import Dict, Any
from datetime import datetime

# Optional imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add lib directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))

from rag_engine import ServerlessRAGEngine, validate_environment
from vector_client import VectorStoreFactory

def handler(request):
    """
    Vercel serverless function handler for health check endpoint
    
    GET /api/health - Basic health check
    GET /api/health?detailed=true - Detailed health check with component status
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
        detailed = query_params.get('detailed', '').lower() == 'true'
        
        # Basic health check response
        health_response = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Advanced RAG System',
            'version': '1.0.0',
            'environment': os.getenv('VERCEL_ENV', 'development'),
            'region': os.getenv('VERCEL_REGION', 'unknown')
        }
        
        # Detailed health check if requested
        if detailed:
            health_response.update(perform_detailed_health_check())
        else:
            # Quick environment validation
            env_check = validate_environment()
            missing_vars = [var for var, present in env_check.items() if not present]
            
            if missing_vars:
                health_response['status'] = 'degraded'
                health_response['warnings'] = [f'Missing environment variables: {", ".join(missing_vars)}']
        
        # Add response time
        health_response['response_time'] = time.time() - start_time
        
        # Determine HTTP status code
        status_code = 200
        if health_response['status'] == 'unhealthy':
            status_code = 503
        elif health_response['status'] == 'degraded':
            status_code = 200  # Still functional but with warnings
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            },
            'body': json.dumps(health_response)
        }
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Health Check Error: {str(e)}")
        
        return {
            'statusCode': 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': 'Health check failed',
                'details': str(e) if os.getenv('DEBUG') == 'true' else 'Enable DEBUG mode for details'
            })
        }

def perform_detailed_health_check() -> Dict[str, Any]:
    """Perform detailed health check of all system components"""
    detailed_status = {
        'components': {},
        'environment': {},
        'performance': {},
        'warnings': [],
        'errors': []
    }
    
    overall_healthy = True
    
    try:
        # Environment validation
        env_check = validate_environment()
        detailed_status['environment'] = {
            'variables': env_check,
            'missing': [var for var, present in env_check.items() if not present]
        }
        
        if detailed_status['environment']['missing']:
            detailed_status['warnings'].append(f"Missing environment variables: {', '.join(detailed_status['environment']['missing'])}")
            overall_healthy = False
        
        # RAG Engine health check
        try:
            rag_engine = ServerlessRAGEngine()
            rag_health = rag_engine.health_check()
            detailed_status['components']['rag_engine'] = rag_health
            
            if rag_health['status'] != 'healthy':
                overall_healthy = False
                detailed_status['errors'].append('RAG engine is unhealthy')
                
        except Exception as e:
            detailed_status['components']['rag_engine'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            detailed_status['errors'].append(f'RAG engine initialization failed: {str(e)}')
            overall_healthy = False
        
        # Vector Store health check
        try:
            vector_client = VectorStoreFactory.create_from_env()
            vector_healthy = vector_client.health_check()
            vector_stats = vector_client.get_stats()
            
            detailed_status['components']['vector_store'] = {
                'status': 'healthy' if vector_healthy else 'unhealthy',
                'stats': vector_stats,
                'type': vector_stats.get('vector_store_type', 'unknown')
            }
            
            if not vector_healthy:
                overall_healthy = False
                detailed_status['errors'].append('Vector store is unhealthy')
                
        except Exception as e:
            detailed_status['components']['vector_store'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            detailed_status['errors'].append(f'Vector store check failed: {str(e)}')
            overall_healthy = False
        
        # Performance metrics
        detailed_status['performance'] = {
            'cold_start': os.getenv('VERCEL_COLD_START') == '1',
            'memory_usage': get_memory_usage(),
            'startup_time': time.time()  # Approximate
        }
        
        # System information
        detailed_status['system'] = {
            'python_version': sys.version,
            'platform': sys.platform,
            'vercel_env': os.getenv('VERCEL_ENV'),
            'vercel_region': os.getenv('VERCEL_REGION'),
            'function_name': os.getenv('VERCEL_FUNCTION_NAME'),
            'deployment_id': os.getenv('VERCEL_DEPLOYMENT_ID')
        }
        
    except Exception as e:
        detailed_status['errors'].append(f'Detailed health check failed: {str(e)}')
        overall_healthy = False
    
    # Set overall status
    if detailed_status['errors']:
        detailed_status['status'] = 'unhealthy'
    elif detailed_status['warnings']:
        detailed_status['status'] = 'degraded'
    else:
        detailed_status['status'] = 'healthy'
    
    return detailed_status

def get_memory_usage() -> Dict[str, Any]:
    """Get current memory usage information"""
    try:
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                'percent': round(process.memory_percent(), 2)
            }
        else:
            # psutil not available, use basic info
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                'max_rss_mb': round(usage.ru_maxrss / 1024, 2) if sys.platform != 'darwin' else round(usage.ru_maxrss / 1024 / 1024, 2),
                'note': 'Limited memory info (psutil not available)'
            }
    except Exception:
        return {'error': 'Unable to get memory usage'}

# Readiness probe endpoint
def readiness_handler(request):
    """
    Readiness probe - checks if the service is ready to handle requests
    More lightweight than full health check
    """
    try:
        # Quick checks for readiness
        env_check = validate_environment()
        critical_vars = ['GOOGLE_API_KEY', 'PINECONE_API_KEY', 'PINECONE_ENVIRONMENT']
        missing_critical = [var for var in critical_vars if not env_check.get(var)]
        
        if missing_critical:
            return {
                'statusCode': 503,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'ready': False,
                    'reason': f'Missing critical environment variables: {", ".join(missing_critical)}'
                })
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'ready': True,
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 503,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'ready': False,
                'error': str(e)
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
        def __init__(self, method='GET', args=None):
            self.method = method
            self.args = args or {}
    
    print("🧪 Testing Health Check API Endpoint")
    print("=" * 40)
    
    # Test basic health check
    mock_request = MockRequest()
    response = handler(mock_request)
    
    print(f"Basic Health Check Status: {response['statusCode']}")
    if response['statusCode'] in [200, 503]:
        body = json.loads(response['body'])
        print(f"Status: {body['status']}")
        print(f"Service: {body.get('service', 'Unknown')}")
        print(f"Response Time: {body.get('response_time', 0):.3f}s")
        
        if 'warnings' in body:
            print(f"Warnings: {body['warnings']}")
    
    # Test detailed health check
    print("\n" + "=" * 40)
    print("Testing detailed health check...")
    
    detailed_request = MockRequest(args={'detailed': 'true'})
    detailed_response = handler(detailed_request)
    
    if detailed_response['statusCode'] in [200, 503]:
        detailed_body = json.loads(detailed_response['body'])
        print(f"Detailed Status: {detailed_body['status']}")
        
        if 'components' in detailed_body:
            for component, status in detailed_body['components'].items():
                print(f"  {component}: {status.get('status', 'unknown')}")
        
        if 'environment' in detailed_body:
            missing = detailed_body['environment'].get('missing', [])
            if missing:
                print(f"Missing env vars: {missing}")
    
    # Test readiness probe
    print("\n" + "=" * 40)
    print("Testing readiness probe...")
    
    readiness_response = readiness_handler(mock_request)
    readiness_body = json.loads(readiness_response['body'])
    print(f"Ready: {readiness_body.get('ready', False)}")
    
    print("\n✅ Health check endpoint test complete!")