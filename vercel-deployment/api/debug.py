"""
Simple debug endpoint to test Vercel deployment
"""
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Simple response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'message': 'Debug endpoint working!',
            'timestamp': datetime.now().isoformat(),
            'path': self.path,
            'working_dir': os.getcwd(),
            'vercel_env': os.getenv('VERCEL_ENV', 'not-set')
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())