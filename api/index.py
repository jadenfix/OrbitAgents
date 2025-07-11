from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import uuid
import random

# Create the app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for demo (use database in production)
users = {}
workflows = [
    {
        'id': 1,
        'name': 'Property Search Automation',
        'description': 'Automatically search for properties across multiple sites',
        'steps': 5,
        'status': 'active',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 2,
        'name': 'Form Filling Assistant',
        'description': 'Smart form completion with AI assistance',
        'steps': 3,
        'status': 'draft',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 3,
        'name': 'Real Estate Lead Generation',
        'description': 'Automated lead generation from multiple sources',
        'steps': 8,
        'status': 'active',
        'created_at': '2025-01-01T00:00:00Z'
    }
]

@app.route('/health', methods=['GET'])
def health():
    """Simple health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'OrbitAgents API'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'OrbitAgents API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.getenv('NODE_ENV', 'development')
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'error': 'Missing required fields'}), 400
        
        if username in users:
            return jsonify({'error': 'Username already exists'}), 400
        
        user_id = str(uuid.uuid4())
        users[username] = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': password,  # In production, hash this!
            'created_at': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user_id,
                'username': username,
                'email': email
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Missing credentials'}), 400
        
        # Demo authentication - always successful for demo
        if username == 'demo' and password == 'demo':
            return jsonify({
                'token': f'demo-jwt-token-{uuid.uuid4()}',
                'user': {
                    'id': 'demo-user',
                    'username': 'demo',
                    'email': 'demo@orbitagents.com'
                }
            })
        
        # Check stored users
        if username in users and users[username]['password'] == password:
            return jsonify({
                'token': f'jwt-token-{uuid.uuid4()}',
                'user': {
                    'id': users[username]['id'],
                    'username': username,
                    'email': users[username]['email']
                }
            })
        
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/demo', methods=['GET'])
def demo():
    """Demo endpoint for testing"""
    return jsonify({
        'status': 'success',
        'message': 'OrbitAgents API Demo',
        'timestamp': datetime.utcnow().isoformat(),
        'features': [
            'AI Browser Automation',
            'Multi-Agent Orchestration',
            'Vision & OCR Capabilities',
            'Memory & Learning',
            'Policy Guardrails'
        ]
    })

@app.route('/api/search', methods=['POST'])
def search():
    """Search endpoint"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Demo search results with variety
        results = [
            {
                'id': 1,
                'title': f'Modern Apartment matching "{query}"',
                'description': f'Beautiful modern apartment perfect for your search: {query}',
                'price': '$2,500/month',
                'location': 'San Francisco, CA',
                'type': 'apartment',
                'bedrooms': 2,
                'bathrooms': 2,
                'sqft': 1200,
                'image_url': 'https://via.placeholder.com/300x200/4f46e5/white?text=Apartment'
            },
            {
                'id': 2,
                'title': f'Family House for "{query}"',
                'description': f'Spacious family house that matches your criteria: {query}',
                'price': '$450,000',
                'location': 'Austin, TX',
                'type': 'house',
                'bedrooms': 3,
                'bathrooms': 2,
                'sqft': 1800,
                'image_url': 'https://via.placeholder.com/300x200/10b981/white?text=House'
            },
            {
                'id': 3,
                'title': f'Luxury Condo for "{query}"',
                'description': f'Premium luxury condo that fits your search: {query}',
                'price': '$3,200/month',
                'location': 'Miami, FL',
                'type': 'condo',
                'bedrooms': 2,
                'bathrooms': 2,
                'sqft': 1400,
                'image_url': 'https://via.placeholder.com/300x200/f59e0b/white?text=Condo'
            }
        ]
        
        return jsonify({
            'query': query,
            'results': results[:2 if 'quick' in query.lower() else 3],
            'total': len(results),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/browser-agent/workflows', methods=['GET'])
def get_workflows():
    """Get browser automation workflows"""
    try:
        return jsonify({
            'workflows': workflows,
            'total': len(workflows),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Workflows error: {str(e)}")
        return jsonify({'error': 'Failed to fetch workflows'}), 500

@app.route('/api/browser-agent/execute', methods=['POST'])
def execute_workflow():
    """Execute browser automation workflow"""
    try:
        data = request.get_json()
        workflow_id = data.get('workflow_id')
        
        if not workflow_id:
            return jsonify({'error': 'Workflow ID is required'}), 400
        
        execution_id = str(uuid.uuid4())
        
        return jsonify({
            'workflow_id': workflow_id,
            'execution_id': execution_id,
            'status': 'running',
            'message': 'Workflow execution started successfully',
            'timestamp': datetime.utcnow().isoformat(),
            'estimated_duration': f"{random.randint(30, 180)} seconds"
        })
        
    except Exception as e:
        logger.error(f"Execution error: {str(e)}")
        return jsonify({'error': 'Workflow execution failed'}), 500

@app.route('/api/browser-agent/status/<execution_id>', methods=['GET'])
def get_execution_status(execution_id):
    """Get execution status"""
    try:
        statuses = ['running', 'completed', 'failed', 'pending']
        return jsonify({
            'execution_id': execution_id,
            'status': random.choice(statuses),
            'progress': random.randint(0, 100),
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

# Remove serverless handler, Vercel will use the WSGI app 'app'

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))  # Changed default from 5000 to 8080
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting OrbitAgents API on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
