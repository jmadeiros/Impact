"""
Health Check API Endpoint for Vercel Deployment
With debugging information to troubleshoot deployment issues
"""
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Collect debug information
            debug_info = {
                'request': {
                    'path': self.path,
                    'method': self.command,
                    'headers': dict(self.headers)
                },
                'server': {
                    'python_version': sys.version,
                    'working_directory': os.getcwd(),
                    'file_location': __file__,
                    'sys_path': sys.path[:5]  # First 5 entries
                },
                'environment': {
                    'VERCEL_ENV': os.getenv('VERCEL_ENV'),
                    'VERCEL_REGION': os.getenv('VERCEL_REGION'),
                    'VERCEL_DEPLOYMENT_ID': os.getenv('VERCEL_DEPLOYMENT_ID'),
                    'PYTHONPATH': os.getenv('PYTHONPATH'),
                    'PWD': os.getenv('PWD')
                },
                'files': {
                    'current_dir_files': os.listdir('.') if os.path.exists('.') else 'N/A',
                    'api_dir_exists': os.path.exists('api'),
                    'vercel_deployment_exists': os.path.exists('vercel-deployment')
                }
            }
            
            # Basic health response
            health_response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'RAG Survey System',
                'version': '1.0.0',
                'message': 'Service is running successfully!',
                'debug': debug_info
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response_body = json.dumps(health_response, indent=2)
            self.wfile.write(response_body.encode())
            
        except Exception as e:
            # Error response with debug info
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'error_type': type(e).__name__,
                'debug': {
                    'working_directory': os.getcwd(),
                    'file_location': __file__,
                    'python_version': sys.version
                }
            }
            
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

# For local testing
if __name__ == "__main__":
    print("🧪 Testing health check endpoint")
    
    # Mock the BaseHTTPRequestHandler for testing
    class MockHandler(handler):
        def __init__(self):
            self.path = '/health'
            self.command = 'GET'
            self.headers = {}
            self.response_data = []
            self.response_code = None
            self.response_headers = {}
        
        def send_response(self, code):
            self.response_code = code
        
        def send_header(self, key, value):
            self.response_headers[key] = value
        
        def end_headers(self):
            pass
        
        def wfile_write(self, data):
            self.response_data.append(data.decode())
        
        # Override wfile to capture output
        class MockWFile:
            def __init__(self, handler):
                self.handler = handler
            
            def write(self, data):
                self.handler.response_data.append(data.decode())
        
        @property
        def wfile(self):
            return self.MockWFile(self)
    
    mock_handler = MockHandler()
    mock_handler.do_GET()
    
    print(f"Response Code: {mock_handler.response_code}")
    print(f"Headers: {mock_handler.response_headers}")
    print(f"Body: {''.join(mock_handler.response_data)}")
    print("✅ Test complete!")