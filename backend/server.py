from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import os
from crawler import run_crawl
from asgiref.wsgi import WsgiToAsgi

# Initialize Flask app with frontend directory as static folder
app = Flask(__name__, static_folder='../frontend')
CORS(app)  # Enable CORS for all routes

# Convert WSGI app to ASGI for async support
asgi_app = WsgiToAsgi(app)

# Serve frontend static files
@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

# Serve other static files
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/crawl', methods=['POST'])
async def crawl():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'status': 'error',
                'message': 'URL is required'
            }), 400
            
        url = data['url']
        depth = int(data.get('depth', 1))  # Default depth is 1
        
        # Run the crawler
        results = await run_crawl(url=url, max_depth=depth)
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error during crawl: {str(e)}")  # Add logging
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Create crawls directory if it doesn't exist
    os.makedirs('../crawls', exist_ok=True)
    
    print(f"Server running at http://localhost:8080")
    # Use Flask's development server for simplicity during development
    app.run(debug=True, port=8080) 