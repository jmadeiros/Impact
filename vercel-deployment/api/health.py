"""
Health Check API Endpoint for Vercel Deployment
Minimal health check without complex dependencies
"""
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """
    Minimal Vercel serverless function handler for health check
    """
    try:
        # Basic health response
        health_response = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'RAG Survey System',
            'version': '1.0.0',
            'message': 'Service is running'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(health_response)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
        }

# For local testing
if __name__ == "__main__":
    print("🧪 Testing minimal health check")
    
    class MockRequest:
        pass
    
    response = handler(MockRequest())
    print(f"Status: {response['statusCode']}")
    print(f"Body: {response['body']}")
    print("✅ Test complete!")