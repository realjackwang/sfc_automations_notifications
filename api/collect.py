import os
import json
import requests
from http.server import BaseHTTPRequestHandler

# Your environment variables from Vercel
KV_REST_API_URL = os.environ.get('KV_REST_API_URL')
KV_REST_API_TOKEN = os.environ.get('KV_REST_API_TOKEN')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read the request body and parse JSON
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Validate required parameters
            required_params = ['source', 'task_name', 'status', 'message']
            if not all(p in data for p in required_params):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing required parameters"}).encode('utf-8'))
                return

            # Construct payload for Upstash KV
            timestamp = data.get('timestamp', os.time())
            key = f"task:{timestamp}"
            
            payload = {
                "command": ["SET", key, json.dumps(data)]
            }
            
            # Send data to Upstash KV REST API
            headers = {
                'Authorization': f'Bearer {KV_REST_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            response = requests.post(KV_REST_API_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                self.send_response(response.status_code)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Failed to store data"}).encode('utf-8'))
                return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Data collected successfully"}).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Internal Server Error: {str(e)}"}).encode('utf-8'))