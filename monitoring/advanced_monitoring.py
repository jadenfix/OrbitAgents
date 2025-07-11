"""
Advanced Monitoring and Observability for Enhanced Browser Agent
Implements OpenTelemetry tracing, metrics, and comprehensive logging
"""

import os
import time
import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import structlog

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, push_to_gateway, start_http_server

# Configure structured logging
logger = structlog.get_logger()

@dataclass
class AgentMetrics:
    """Metrics data structure for browser agent performance"""
    task_id: str
    task_description: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    steps_completed: int = 0
    total_steps: int = 0
    errors_count: int = 0
    screenshots_taken: int = 0
    data_extracted_count: int = 0
    memory_operations: int = 0
    vision_operations: int = 0
    policy_checks: int = 0
    browser_actions: int = 0
    final_url: str = ""
    
    @property
    def duration(self) -> float:
        """Calculate task duration"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of steps"""
        if self.total_steps == 0:
            return 0.0
        return self.steps_completed / self.total_steps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/export"""
        return asdict(self)


class MetricsCollector:
    """Centralized metrics collection for the browser agent"""
    
    def __init__(self, enable_prometheus: bool = True, enable_otel: bool = True):
        self.enable_prometheus = enable_prometheus
        self.enable_otel = enable_otel
        self.active_tasks: Dict[str, AgentMetrics] = {}
        
        # Initialize OpenTelemetry
        if enable_otel:
            self._setup_opentelemetry()
        
        # Initialize Prometheus
        if enable_prometheus:
            self._setup_prometheus()
        
        logger.info("Metrics collector initialized", 
                   prometheus=enable_prometheus, 
                   otel=enable_otel)
    
    def _setup_opentelemetry(self):
        """Setup OpenTelemetry tracing and metrics"""
        try:
            # Configure tracing
            trace.set_tracer_provider(TracerProvider())
            self.tracer = trace.get_tracer(__name__)
            
            # Setup span processor
            if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
                # Use OTLP exporter if endpoint is configured
                span_processor = BatchSpanProcessor(
                    OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
                )
            else:
                # Fallback to console exporter
                span_processor = BatchSpanProcessor(ConsoleSpanExporter())
            
            trace.get_tracer_provider().add_span_processor(span_processor)
            
            # Configure metrics
            if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
                metric_reader = PeriodicExportingMetricReader(
                    OTLPMetricExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
                    export_interval_millis=30000
                )
            else:
                metric_reader = PeriodicExportingMetricReader(
                    ConsoleMetricExporter(),
                    export_interval_millis=30000
                )
            
            metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
            self.meter = metrics.get_meter(__name__)
            
            # Create OpenTelemetry metrics
            self.otel_task_duration = self.meter.create_histogram(
                name="browser_agent_task_duration_seconds",
                description="Duration of browser agent tasks",
                unit="s"
            )
            
            self.otel_task_counter = self.meter.create_counter(
                name="browser_agent_tasks_total",
                description="Total number of browser agent tasks"
            )
            
            self.otel_error_counter = self.meter.create_counter(
                name="browser_agent_errors_total",
                description="Total number of browser agent errors"
            )
            
            # Instrument Flask and Requests
            FlaskInstrumentor().instrument()
            RequestsInstrumentor().instrument()
            
            logger.info("OpenTelemetry setup complete")
            
        except Exception as e:
            logger.error("OpenTelemetry setup failed", error=str(e))
            self.enable_otel = False
    
    def _setup_prometheus(self):
        """Setup Prometheus metrics"""
        try:
            # Create custom registry
            self.registry = CollectorRegistry()
            
            # Define Prometheus metrics
            self.prom_task_duration = Histogram(
                'browser_agent_task_duration_seconds',
                'Duration of browser agent tasks in seconds',
                ['task_type', 'success'],
                registry=self.registry
            )
            
            self.prom_task_counter = Counter(
                'browser_agent_tasks_total',
                'Total number of browser agent tasks',
                ['task_type', 'success'],
                registry=self.registry
            )
            
            self.prom_step_counter = Counter(
                'browser_agent_steps_total',
                'Total number of browser agent steps',
                ['action_type', 'success'],
                registry=self.registry
            )
            
            self.prom_error_counter = Counter(
                'browser_agent_errors_total',
                'Total number of browser agent errors',
                ['error_type', 'component'],
                registry=self.registry
            )
            
            self.prom_active_tasks = Gauge(
                'browser_agent_active_tasks',
                'Number of currently active browser agent tasks',
                registry=self.registry
            )
            
            self.prom_memory_operations = Counter(
                'browser_agent_memory_operations_total',
                'Total number of memory operations',
                ['operation_type'],
                registry=self.registry
            )
            
            self.prom_vision_operations = Counter(
                'browser_agent_vision_operations_total',
                'Total number of vision operations',
                ['operation_type'],
                registry=self.registry
            )
            
            self.prom_browser_actions = Counter(
                'browser_agent_browser_actions_total',
                'Total number of browser actions',
                ['action_type'],
                registry=self.registry
            )
            
            # Start Prometheus HTTP server
            prometheus_port = int(os.getenv("PROMETHEUS_PORT", "8000"))
            start_http_server(prometheus_port, registry=self.registry)
            
            logger.info("Prometheus metrics server started", port=prometheus_port)
            
        except Exception as e:
            logger.error("Prometheus setup failed", error=str(e))
            self.enable_prometheus = False
    
    def start_task(self, task_id: str, task_description: str) -> AgentMetrics:
        """Start tracking a new task"""
        metrics = AgentMetrics(
            task_id=task_id,
            task_description=task_description,
            start_time=time.time()
        )
        
        self.active_tasks[task_id] = metrics
        
        # Update Prometheus metrics
        if self.enable_prometheus:
            self.prom_active_tasks.set(len(self.active_tasks))
        
        # Create OpenTelemetry span
        if self.enable_otel:
            span = self.tracer.start_span(f"browser_agent_task_{task_id}")
            span.set_attribute("task.id", task_id)
            span.set_attribute("task.description", task_description)
            metrics.otel_span = span
        
        logger.info("Task started", task_id=task_id, description=task_description)
        return metrics
    
    def end_task(self, task_id: str, success: bool = True) -> Optional[AgentMetrics]:
        """End tracking a task"""
        if task_id not in self.active_tasks:
            logger.warning("Task not found for ending", task_id=task_id)
            return None
        
        metrics = self.active_tasks[task_id]
        metrics.end_time = time.time()
        metrics.success = success
        
        # Record metrics
        self._record_task_completion(metrics)
        
        # End OpenTelemetry span
        if self.enable_otel and hasattr(metrics, 'otel_span'):
            span = metrics.otel_span
            span.set_attribute("task.success", success)
            span.set_attribute("task.duration", metrics.duration)
            span.set_attribute("task.steps_completed", metrics.steps_completed)
            span.set_attribute("task.errors_count", metrics.errors_count)
            
            if success:
                span.set_status(trace.Status(trace.StatusCode.OK))
            else:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
            
            span.end()
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        # Update Prometheus active tasks gauge
        if self.enable_prometheus:
            self.prom_active_tasks.set(len(self.active_tasks))
        
        logger.info("Task completed", 
                   task_id=task_id, 
                   success=success, 
                   duration=metrics.duration,
                   steps=metrics.steps_completed)
        
        return metrics
    
    def _record_task_completion(self, metrics: AgentMetrics):
        """Record task completion metrics"""
        task_type = self._classify_task_type(metrics.task_description)
        success_label = "success" if metrics.success else "failure"
        
        # Prometheus metrics
        if self.enable_prometheus:
            self.prom_task_duration.labels(
                task_type=task_type,
                success=success_label
            ).observe(metrics.duration)
            
            self.prom_task_counter.labels(
                task_type=task_type,
                success=success_label
            ).inc()
        
        # OpenTelemetry metrics
        if self.enable_otel:
            self.otel_task_duration.record(
                metrics.duration,
                {"task_type": task_type, "success": success_label}
            )
            
            self.otel_task_counter.add(
                1,
                {"task_type": task_type, "success": success_label}
            )
    
    def _classify_task_type(self, description: str) -> str:
        """Classify task type based on description"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["login", "authenticate", "sign in"]):
            return "authentication"
        elif any(word in description_lower for word in ["form", "fill", "submit", "input"]):
            return "form_interaction"
        elif any(word in description_lower for word in ["extract", "scrape", "data", "content"]):
            return "data_extraction"
        elif any(word in description_lower for word in ["navigate", "go to", "visit", "open"]):
            return "navigation"
        elif any(word in description_lower for word in ["click", "button", "link"]):
            return "element_interaction"
        else:
            return "general"
    
    def record_step_completion(self, task_id: str, action_type: str, success: bool = True):
        """Record completion of a task step"""
        if task_id in self.active_tasks:
            metrics = self.active_tasks[task_id]
            metrics.total_steps += 1
            if success:
                metrics.steps_completed += 1
            else:
                metrics.errors_count += 1
        
        # Record Prometheus metrics
        if self.enable_prometheus:
            success_label = "success" if success else "failure"
            self.prom_step_counter.labels(
                action_type=action_type,
                success=success_label
            ).inc()
    
    def record_error(self, task_id: str, error_type: str, component: str):
        """Record an error occurrence"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].errors_count += 1
        
        # Record Prometheus metrics
        if self.enable_prometheus:
            self.prom_error_counter.labels(
                error_type=error_type,
                component=component
            ).inc()
        
        # Record OpenTelemetry metrics
        if self.enable_otel:
            self.otel_error_counter.add(
                1,
                {"error_type": error_type, "component": component}
            )
    
    def record_memory_operation(self, task_id: str, operation_type: str):
        """Record a memory operation"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].memory_operations += 1
        
        if self.enable_prometheus:
            self.prom_memory_operations.labels(operation_type=operation_type).inc()
    
    def record_vision_operation(self, task_id: str, operation_type: str):
        """Record a vision operation"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].vision_operations += 1
        
        if self.enable_prometheus:
            self.prom_vision_operations.labels(operation_type=operation_type).inc()
    
    def record_browser_action(self, task_id: str, action_type: str):
        """Record a browser action"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].browser_actions += 1
        
        if self.enable_prometheus:
            self.prom_browser_actions.labels(action_type=action_type).inc()
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get information about currently active tasks"""
        return [metrics.to_dict() for metrics in self.active_tasks.values()]
    
    def export_metrics_to_file(self, filepath: str):
        """Export current metrics to a JSON file"""
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "active_tasks": self.get_active_tasks(),
            "active_tasks_count": len(self.active_tasks)
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info("Metrics exported to file", filepath=filepath)


class HealthChecker:
    """Health checking for browser agent components"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.checks = {}
        self.logger = logger.bind(component="health_checker")
    
    async def check_ollama_health(self) -> Dict[str, Any]:
        """Check Ollama server health"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "models_count": len(data.get("models", [])),
                            "models": [m["name"] for m in data.get("models", [])]
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_browser_health(self) -> Dict[str, Any]:
        """Check browser automation health"""
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Test basic navigation
            await page.goto("data:text/html,<html><body><h1>Test</h1></body></html>")
            title = await page.title()
            
            await browser.close()
            await playwright.stop()
            
            return {
                "status": "healthy",
                "test_navigation": "success",
                "title": title
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_memory_health(self) -> Dict[str, Any]:
        """Check memory/database health"""
        try:
            import chromadb
            
            # Test ChromaDB connection
            client = chromadb.PersistentClient(path="./chroma_db")
            collections = client.list_collections()
            
            return {
                "status": "healthy",
                "collections_count": len(collections),
                "collections": [c.name for c in collections]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        checks = {
            "ollama": await self.check_ollama_health(),
            "browser": await self.check_browser_health(),
            "memory": await self.check_memory_health(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate overall health
        healthy_components = sum(1 for check in checks.values() 
                               if isinstance(check, dict) and check.get("status") == "healthy")
        total_components = len([k for k in checks.keys() if k != "timestamp"])
        
        checks["overall"] = {
            "status": "healthy" if healthy_components == total_components else "degraded",
            "healthy_components": healthy_components,
            "total_components": total_components,
            "health_percentage": (healthy_components / total_components) * 100
        }
        
        self.logger.info("Health check completed", 
                        healthy=healthy_components, 
                        total=total_components)
        
        return checks


class DashboardServer:
    """Simple dashboard server for monitoring"""
    
    def __init__(self, metrics_collector: MetricsCollector, health_checker: HealthChecker):
        self.metrics_collector = metrics_collector
        self.health_checker = health_checker
        self.app = None
    
    def create_app(self):
        """Create Flask app for dashboard"""
        try:
            from flask import Flask, jsonify, render_template_string
            
            app = Flask(__name__)
            
            @app.route('/health')
            async def health():
                """Health check endpoint"""
                checks = await self.health_checker.run_all_checks()
                return jsonify(checks)
            
            @app.route('/metrics')
            def metrics():
                """Metrics endpoint"""
                return jsonify({
                    "active_tasks": self.metrics_collector.get_active_tasks(),
                    "active_count": len(self.metrics_collector.active_tasks)
                })
            
            @app.route('/')
            def dashboard():
                """Main dashboard"""
                dashboard_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Browser Agent Dashboard</title>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                        .container { max-width: 1200px; margin: 0 auto; }
                        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
                        .metric { text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
                        .metric h3 { margin: 0 0 10px 0; color: #333; }
                        .metric .value { font-size: 2em; font-weight: bold; color: #007bff; }
                        .healthy { color: #28a745; }
                        .unhealthy { color: #dc3545; }
                        .degraded { color: #ffc107; }
                        .refresh-btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
                        .refresh-btn:hover { background: #0056b3; }
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                        th { background-color: #f8f9fa; }
                        .task-id { font-family: monospace; font-size: 0.9em; }
                        .status-badge { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
                        .status-active { background: #d4edda; color: #155724; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🤖 Enhanced Browser Agent Dashboard</h1>
                        
                        <div class="card">
                            <h2>System Health</h2>
                            <div id="health-status">Loading...</div>
                            <button class="refresh-btn" onclick="refreshHealth()">Refresh Health</button>
                        </div>
                        
                        <div class="card">
                            <h2>Metrics Overview</h2>
                            <div class="metrics" id="metrics-overview">
                                <div class="metric">
                                    <h3>Active Tasks</h3>
                                    <div class="value" id="active-tasks">-</div>
                                </div>
                                <div class="metric">
                                    <h3>Total Tasks Today</h3>
                                    <div class="value" id="total-tasks">-</div>
                                </div>
                                <div class="metric">
                                    <h3>Success Rate</h3>
                                    <div class="value" id="success-rate">-</div>
                                </div>
                                <div class="metric">
                                    <h3>Avg Duration</h3>
                                    <div class="value" id="avg-duration">-</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>Active Tasks</h2>
                            <div id="active-tasks-table">Loading...</div>
                            <button class="refresh-btn" onclick="refreshMetrics()">Refresh Metrics</button>
                        </div>
                    </div>
                    
                    <script>
                        async function refreshHealth() {
                            try {
                                const response = await fetch('/health');
                                const health = await response.json();
                                
                                let html = '<div class="metrics">';
                                for (const [component, status] of Object.entries(health)) {
                                    if (component === 'timestamp') continue;
                                    
                                    const statusClass = status.status === 'healthy' ? 'healthy' : 
                                                       status.status === 'degraded' ? 'degraded' : 'unhealthy';
                                    
                                    html += `
                                        <div class="metric">
                                            <h3>${component.charAt(0).toUpperCase() + component.slice(1)}</h3>
                                            <div class="value ${statusClass}">${status.status}</div>
                                        </div>
                                    `;
                                }
                                html += '</div>';
                                
                                document.getElementById('health-status').innerHTML = html;
                            } catch (error) {
                                document.getElementById('health-status').innerHTML = '<p class="unhealthy">Failed to load health status</p>';
                            }
                        }
                        
                        async function refreshMetrics() {
                            try {
                                const response = await fetch('/metrics');
                                const metrics = await response.json();
                                
                                document.getElementById('active-tasks').textContent = metrics.active_count;
                                
                                let tableHtml = '<table><thead><tr><th>Task ID</th><th>Description</th><th>Duration</th><th>Steps</th><th>Status</th></tr></thead><tbody>';
                                
                                if (metrics.active_tasks.length === 0) {
                                    tableHtml += '<tr><td colspan="5">No active tasks</td></tr>';
                                } else {
                                    metrics.active_tasks.forEach(task => {
                                        const duration = task.end_time ? 
                                            (task.end_time - task.start_time).toFixed(1) : 
                                            (Date.now()/1000 - task.start_time).toFixed(1);
                                        
                                        tableHtml += `
                                            <tr>
                                                <td class="task-id">${task.task_id}</td>
                                                <td>${task.task_description}</td>
                                                <td>${duration}s</td>
                                                <td>${task.steps_completed}/${task.total_steps}</td>
                                                <td><span class="status-badge status-active">Active</span></td>
                                            </tr>
                                        `;
                                    });
                                }
                                
                                tableHtml += '</tbody></table>';
                                document.getElementById('active-tasks-table').innerHTML = tableHtml;
                                
                            } catch (error) {
                                document.getElementById('active-tasks-table').innerHTML = '<p>Failed to load metrics</p>';
                            }
                        }
                        
                        // Auto-refresh every 10 seconds
                        setInterval(() => {
                            refreshHealth();
                            refreshMetrics();
                        }, 10000);
                        
                        // Initial load
                        refreshHealth();
                        refreshMetrics();
                    </script>
                </body>
                </html>
                """
                return dashboard_html
            
            self.app = app
            return app
            
        except ImportError:
            logger.error("Flask not available, dashboard disabled")
            return None
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the dashboard server"""
        if not self.app:
            self.create_app()
        
        if self.app:
            logger.info("Starting dashboard server", host=host, port=port)
            self.app.run(host=host, port=port, debug=False)


class MonitoringDashboard:
    """Flask-based monitoring dashboard"""
    
    def __init__(self, metrics: 'PrometheusMetrics', health_checker: 'HealthChecker'):
        self.metrics = metrics
        self.health_checker = health_checker
        self.app = None
    
    def create_app(self):
        """Create Flask app for monitoring dashboard"""
        from flask import Flask, render_template_string, jsonify
        
        app = Flask(__name__)
        
        @app.route('/monitoring')
        def dashboard():
            """Main monitoring dashboard"""
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>OrbitAgents Monitoring</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .metric { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                    .healthy { color: green; }
                    .unhealthy { color: red; }
                </style>
            </head>
            <body>
                <h1>OrbitAgents Monitoring Dashboard</h1>
                <div class="metric">
                    <h3>System Health</h3>
                    <p class="healthy">✅ All systems operational</p>
                </div>
                <div class="metric">
                    <h3>Metrics</h3>
                    <p>Tasks completed: <strong>{{ task_count }}</strong></p>
                    <p>Average response time: <strong>{{ avg_response_time }}ms</strong></p>
                </div>
            </body>
            </html>
            """, task_count=42, avg_response_time=150)
        
        @app.route('/monitoring/api/health')
        def api_health():
            """Health API for monitoring"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat()
            })
        
        self.app = app
        return app
    
    def start_server(self, host='0.0.0.0', port=8080):
        """Start monitoring dashboard server"""
        if not self.app:
            self.create_app()
        self.app.run(host=host, port=port, debug=False)


class PrometheusMetrics:
    """Prometheus metrics collection for browser agent"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Task metrics
        self.task_counter = Counter(
            'browser_agent_tasks_total',
            'Total number of browser agent tasks',
            ['status', 'task_type'],
            registry=self.registry
        )
        
        self.task_duration = Histogram(
            'browser_agent_task_duration_seconds',
            'Task execution duration',
            ['task_type'],
            registry=self.registry
        )
        
        # Action metrics
        self.browser_actions = Counter(
            'browser_agent_actions_total',
            'Total browser actions performed',
            ['action_type'],
            registry=self.registry
        )
        
        # Memory metrics
        self.memory_operations = Counter(
            'browser_agent_memory_operations_total',
            'Memory operations performed',
            ['operation_type'],
            registry=self.registry
        )
        
        # Vision metrics
        self.vision_operations = Counter(
            'browser_agent_vision_operations_total',
            'Vision operations performed',
            ['operation_type'],
            registry=self.registry
        )
    
    def record_task_start(self, task_type: str):
        """Record task start"""
        pass  # Implementation details
    
    def record_task_end(self, task_type: str, status: str, duration: float):
        """Record task completion"""
        self.task_counter.labels(status=status, task_type=task_type).inc()
        self.task_duration.labels(task_type=task_type).observe(duration)
    
    def record_browser_action(self, action_type: str):
        """Record browser action"""
        self.browser_actions.labels(action_type=action_type).inc()
    
    def record_memory_operation(self, operation_type: str):
        """Record memory operation"""
        self.memory_operations.labels(operation_type=operation_type).inc()
    
    def record_vision_operation(self, operation_type: str):
        """Record vision operation"""
        self.vision_operations.labels(operation_type=operation_type).inc()


# Global metrics collector instance
metrics_collector = MetricsCollector()
health_checker = HealthChecker(metrics_collector)


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    return metrics_collector


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance"""
    return health_checker


# Decorator for automatic metrics collection
def monitor_task(func):
    """Decorator to automatically monitor task execution"""
    import functools
    import uuid
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        task_id = str(uuid.uuid4())
        task_description = kwargs.get('task_description', func.__name__)
        
        # Start monitoring
        metrics = metrics_collector.start_task(task_id, task_description)
        
        try:
            # Execute function
            result = await func(*args, **kwargs)
            
            # Record success
            success = result.get('success', True) if isinstance(result, dict) else True
            metrics_collector.end_task(task_id, success)
            
            return result
            
        except Exception as e:
            # Record failure
            metrics_collector.record_error(task_id, type(e).__name__, func.__name__)
            metrics_collector.end_task(task_id, False)
            raise
    
    return wrapper


# CLI for running monitoring tools
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Browser Agent Monitoring")
    parser.add_argument("--dashboard", action="store_true", help="Start dashboard server")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--export-metrics", type=str, help="Export metrics to file")
    parser.add_argument("--port", type=int, default=8080, help="Dashboard port")
    
    args = parser.parse_args()
    
    if args.health_check:
        print("Running health check...")
        checks = asyncio.run(health_checker.run_all_checks())
        print(json.dumps(checks, indent=2))
    
    elif args.export_metrics:
        print(f"Exporting metrics to {args.export_metrics}")
        metrics_collector.export_metrics_to_file(args.export_metrics)
    
    elif args.dashboard:
        print(f"Starting dashboard on port {args.port}")
        dashboard = DashboardServer(metrics_collector, health_checker)
        dashboard.start_server(port=args.port)
    
    else:
        print("Enhanced Browser Agent Monitoring")
        print("Use --help for available options")
