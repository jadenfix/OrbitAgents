from flask import Flask, jsonify, request
from flask_cors import CORS

try:
    from api.gateway import forward
except ModuleNotFoundError:
    from gateway import forward
import os
import logging
from datetime import datetime
import uuid

# Create the app
app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 65536

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/", methods=["GET"])
def root():
    """Root endpoint with API information"""
    return jsonify(
        {
            "message": "OrbitAgents API Server",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat(),
            "endpoints": {
                "health": "/health",
                "demo": "/api/demo",
                "api": {
                    "auth": "/api/auth/*",
                    "workflows": "/api/workflows",
                    "browser_actions": "/api/browser-actions/*",
                    "monitoring": "/api/monitoring/*",
                },
            },
            "frontend_url": "http://localhost:3001",
            "monitoring_dashboard": "http://localhost:9090",
            "documentation": "https://github.com/jadenfix/Orbit",
        }
    )


# In-memory storage for demo (use database in production)
workflows = [
    {
        "id": 1,
        "name": "Property Search Automation",
        "description": "Automatically search for properties across multiple sites",
        "steps": 5,
        "status": "unconfigured",
        "created_at": "2025-01-01T00:00:00Z",
    },
    {
        "id": 2,
        "name": "Form Filling Assistant",
        "description": "Smart form completion with AI assistance",
        "steps": 3,
        "status": "draft",
        "created_at": "2025-01-01T00:00:00Z",
    },
    {
        "id": 3,
        "name": "Real Estate Lead Generation",
        "description": "Automated lead generation from multiple sources",
        "steps": 8,
        "status": "unconfigured",
        "created_at": "2025-01-01T00:00:00Z",
    },
]


@app.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "OrbitAgents API",
        }
    )


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "OrbitAgents API",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv("NODE_ENV", "development"),
            "scope": "gateway_liveness_only",
            "auth_configured": bool(os.getenv("AUTH_SERVICE_URL")),
            "query_configured": bool(os.getenv("QUERY_SERVICE_URL")),
            "browser_execution": "unconfigured",
        }
    )


@app.route("/api/auth/<endpoint>", methods=["GET", "POST"])
def auth_proxy(endpoint):
    if (request.method, endpoint) not in {
        ("POST", "register"),
        ("POST", "login"),
        ("GET", "me"),
        ("GET", "healthz"),
    }:
        return jsonify({"detail": "Unknown authentication operation"}), 404
    return forward("AUTH_SERVICE_URL", endpoint)


@app.route("/api/query/<endpoint>", methods=["GET", "POST"])
def query_proxy(endpoint):
    if (request.method, endpoint) not in {
        ("POST", "search_pipeline"),
        ("GET", "health"),
    }:
        return jsonify({"detail": "Unknown query operation"}), 404
    return forward("QUERY_SERVICE_URL", endpoint)


@app.route("/api/demo", methods=["GET"])
def demo():
    """Demo endpoint for testing"""
    return jsonify(
        {
            "status": "information_only",
            "message": "This endpoint describes planned capabilities; no agents or search ran",
            "timestamp": datetime.utcnow().isoformat(),
            "features": [
                "AI Browser Automation",
                "Multi-Agent Orchestration",
                "Vision & OCR Capabilities",
                "Memory & Learning",
                "Policy Guardrails",
            ],
        }
    )


@app.route("/api/search", methods=["POST"])
def search():
    return (
        jsonify(
            {
                "detail": "Use /api/query/search_pipeline with a configured query service."
            }
        ),
        410,
    )


@app.route("/api/browser-agent/workflows", methods=["GET"])
def get_workflows():
    """Get browser automation workflows"""
    try:
        return jsonify(
            {
                "workflows": workflows,
                "total": len(workflows),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        logger.error(f"Workflows error: {str(e)}")
        return jsonify({"error": "Failed to fetch workflows"}), 500


@app.route("/api/browser-agent/execute", methods=["POST"])
def execute_workflow():
    return (
        jsonify(
            {"detail": "Browser execution is not configured. No workflow was started."}
        ),
        503,
    )


@app.route("/api/browser-agent/status/<execution_id>", methods=["GET"])
def get_execution_status(execution_id):
    return jsonify({"detail": "No execution record exists for this ID."}), 404


# Remove serverless handler, Vercel will use the WSGI app 'app'

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))  # Changed default from 5000 to 8080
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    logger.info(f"Starting OrbitAgents API on port {port}")
    logger.info(f"Debug mode: {debug}")

    app.run(host="0.0.0.0", port=port, debug=debug)
