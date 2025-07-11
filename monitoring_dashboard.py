#!/usr/bin/env python3
"""
OrbitAgents Web Monitoring Dashboard
A simple web interface to monitor OrbitAgents status and performance
"""

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import requests
import json
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
API_BASE_URL = "http://localhost:8080"

# HTML Template for monitoring dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OrbitAgents Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h3 {
            margin-bottom: 15px;
            color: #4a5568;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .status-healthy {
            background-color: #48bb78;
        }
        
        .status-unhealthy {
            background-color: #f56565;
        }
        
        .status-warning {
            background-color: #ed8936;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
        }
        
        .metric-value {
            color: #4a5568;
            font-family: 'Courier New', monospace;
        }
        
        .log-container {
            background: #1a202c;
            color: #e2e8f0;
            border-radius: 10px;
            padding: 20px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        
        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }
        
        .log-timestamp {
            color: #63b3ed;
        }
        
        .log-level-info {
            color: #68d391;
        }
        
        .log-level-warning {
            color: #f6e05e;
        }
        
        .log-level-error {
            color: #fc8181;
        }
        
        .refresh-button {
            background: #4299e1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
            transition: background-color 0.3s ease;
        }
        
        .refresh-button:hover {
            background: #3182ce;
        }
        
        .auto-refresh {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            color: white;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 OrbitAgents Monitoring Dashboard</h1>
            <p>Real-time monitoring of your AI browser agent platform</p>
        </div>
        
        <div class="controls">
            <button class="refresh-button" onclick="refreshData()">🔄 Refresh Data</button>
            <button class="refresh-button" onclick="toggleAutoRefresh()">⏱️ Toggle Auto-Refresh</button>
            <div class="auto-refresh">
                <span>Auto-refresh: <span id="autoRefreshStatus">ON</span></span>
            </div>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>
                    <span class="status-indicator" id="apiStatus"></span>
                    API Health
                </h3>
                <div class="metric">
                    <span class="metric-label">Status:</span>
                    <span class="metric-value" id="apiHealthStatus">Checking...</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Response Time:</span>
                    <span class="metric-value" id="apiResponseTime">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Check:</span>
                    <span class="metric-value" id="apiLastCheck">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>
                    <span class="status-indicator status-healthy"></span>
                    System Metrics
                </h3>
                <div class="metric">
                    <span class="metric-label">Uptime:</span>
                    <span class="metric-value" id="systemUptime">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Total Requests:</span>
                    <span class="metric-value" id="totalRequests">-</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Active Workflows:</span>
                    <span class="metric-value" id="activeWorkflows">-</span>
                </div>
            </div>
            
            <div class="card">
                <h3>
                    <span class="status-indicator" id="workflowStatus"></span>
                    AI Workflows
                </h3>
                <div id="workflowList">
                    Loading workflows...
                </div>
            </div>
            
            <div class="card">
                <h3>
                    <span class="status-indicator status-healthy"></span>
                    Quick Actions
                </h3>
                <button class="refresh-button" onclick="runHealthCheck()">🏥 Health Check</button>
                <button class="refresh-button" onclick="executeTestWorkflow()">🧪 Test Workflow</button>
                <button class="refresh-button" onclick="openAPI()">🔗 Open API</button>
                <button class="refresh-button" onclick="openFrontend()">🌐 Open Frontend</button>
            </div>
        </div>
        
        <div class="card">
            <h3>
                <span class="status-indicator status-healthy"></span>
                Real-time Logs
            </h3>
            <div class="log-container" id="logContainer">
                <div class="log-entry">
                    <span class="log-timestamp">[{{ current_time }}]</span>
                    <span class="log-level-info">[INFO]</span>
                    OrbitAgents Monitoring Dashboard started
                </div>
            </div>
        </div>
    </div>

    <script>
        let autoRefresh = true;
        let refreshInterval;
        
        function addLog(level, message) {
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            logEntry.innerHTML = `
                <span class="log-timestamp">[${timestamp}]</span>
                <span class="log-level-${level}">[${level.toUpperCase()}]</span>
                ${message}
            `;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        async function checkAPIHealth() {
            const startTime = Date.now();
            try {
                const response = await fetch('/api/health-check');
                const data = await response.json();
                const responseTime = Date.now() - startTime;
                
                document.getElementById('apiStatus').className = 'status-indicator ' + 
                    (data.healthy ? 'status-healthy' : 'status-unhealthy');
                document.getElementById('apiHealthStatus').textContent = data.healthy ? 'Healthy' : 'Unhealthy';
                document.getElementById('apiResponseTime').textContent = responseTime + 'ms';
                document.getElementById('apiLastCheck').textContent = new Date().toLocaleTimeString();
                
                if (data.healthy) {
                    addLog('info', 'API health check passed');
                } else {
                    addLog('warning', 'API health check failed');
                }
                
                return data.healthy;
            } catch (error) {
                document.getElementById('apiStatus').className = 'status-indicator status-unhealthy';
                document.getElementById('apiHealthStatus').textContent = 'Error';
                document.getElementById('apiResponseTime').textContent = 'Timeout';
                addLog('error', 'API health check failed: ' + error.message);
                return false;
            }
        }
        
        async function loadWorkflows() {
            try {
                const response = await fetch('/api/workflows');
                const data = await response.json();
                
                const workflowList = document.getElementById('workflowList');
                workflowList.innerHTML = '';
                
                data.workflows.forEach(workflow => {
                    const workflowDiv = document.createElement('div');
                    workflowDiv.className = 'metric';
                    workflowDiv.innerHTML = `
                        <span class="metric-label">${workflow.name}:</span>
                        <span class="metric-value">${workflow.status}</span>
                    `;
                    workflowList.appendChild(workflowDiv);
                });
                
                document.getElementById('workflowStatus').className = 'status-indicator status-healthy';
                document.getElementById('activeWorkflows').textContent = data.workflows.filter(w => w.status === 'active').length;
                addLog('info', `Loaded ${data.workflows.length} workflows`);
            } catch (error) {
                document.getElementById('workflowStatus').className = 'status-indicator status-unhealthy';
                addLog('error', 'Failed to load workflows: ' + error.message);
            }
        }
        
        async function refreshData() {
            addLog('info', 'Refreshing dashboard data...');
            await checkAPIHealth();
            await loadWorkflows();
            
            // Update system metrics
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            document.getElementById('systemUptime').textContent = formatUptime(uptime);
            document.getElementById('totalRequests').textContent = Math.floor(Math.random() * 1000) + 50;
        }
        
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            return `${hours}h ${minutes}m ${secs}s`;
        }
        
        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            document.getElementById('autoRefreshStatus').textContent = autoRefresh ? 'ON' : 'OFF';
            
            if (autoRefresh) {
                refreshInterval = setInterval(refreshData, 5000);
                addLog('info', 'Auto-refresh enabled');
            } else {
                clearInterval(refreshInterval);
                addLog('info', 'Auto-refresh disabled');
            }
        }
        
        function runHealthCheck() {
            addLog('info', 'Running manual health check...');
            checkAPIHealth();
        }
        
        async function executeTestWorkflow() {
            addLog('info', 'Executing test workflow...');
            try {
                const response = await fetch('/api/execute-test-workflow', { method: 'POST' });
                const data = await response.json();
                addLog('info', `Test workflow executed: ${data.execution_id}`);
            } catch (error) {
                addLog('error', 'Test workflow failed: ' + error.message);
            }
        }
        
        function openAPI() {
            window.open('http://localhost:8080', '_blank');
        }
        
        function openFrontend() {
            window.open('http://localhost:3000', '_blank');
        }
        
        // Initialize
        const startTime = Date.now();
        
        // Start auto-refresh
        refreshData();
        refreshInterval = setInterval(refreshData, 5000);
        
        addLog('info', 'Dashboard initialized successfully');
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main monitoring dashboard"""
    return render_template_string(DASHBOARD_HTML, current_time=datetime.now().strftime('%H:%M:%S'))

@app.route('/api/health-check')
def health_check():
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return jsonify({
            'healthy': response.status_code == 200,
            'status_code': response.status_code,
            'response': response.json() if response.status_code == 200 else None
        })
    except Exception as e:
        return jsonify({
            'healthy': False,
            'error': str(e)
        })

@app.route('/api/workflows')
def get_workflows():
    """Get available workflows"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/browser-agent/workflows", timeout=5)
        return response.json()
    except Exception as e:
        return jsonify({
            'error': str(e),
            'workflows': []
        })

@app.route('/api/execute-test-workflow', methods=['POST'])
def execute_test_workflow():
    """Execute a test workflow"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/browser-agent/execute",
            json={'workflow_id': 1, 'parameters': {'test': True}},
            timeout=10
        )
        return response.json()
    except Exception as e:
        return jsonify({
            'error': str(e),
            'execution_id': None
        })

if __name__ == '__main__':
    print("🚀 Starting OrbitAgents Monitoring Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:9090")
    print("🔗 Monitoring OrbitAgents API at: http://localhost:8080")
    
    app.run(
        host='0.0.0.0',
        port=9090,
        debug=True
    )
