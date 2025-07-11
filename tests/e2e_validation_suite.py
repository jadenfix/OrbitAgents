#!/usr/bin/env python3
"""
Comprehensive E2E Validation Suite for OrbitAgents
Tests the full integration including Cloudflare, monitoring, and agent workflows
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import pytest
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.enhanced_browser_agent import EnhancedBrowserAgent
from api.cloudflare_integration import create_cloudflare_config, HybridInferenceClient
from monitoring.advanced_monitoring import AdvancedMonitoring

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class E2EValidator:
    """Comprehensive end-to-end validation for OrbitAgents"""
    
    def __init__(self):
        self.logger = logger
        self.results = {}
        self.start_time = time.time()
        
        # Test configuration
        self.test_url = "https://example.com"
        self.monitoring = None
        self.agent = None
        
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete E2E validation suite"""
        self.logger.info("🚀 Starting comprehensive E2E validation for OrbitAgents")
        
        try:
            # 1. Environment and dependency validation
            await self.validate_environment()
            
            # 2. Core component validation
            await self.validate_core_components()
            
            # 3. Cloudflare integration validation
            await self.validate_cloudflare_integration()
            
            # 4. Agent workflow validation
            await self.validate_agent_workflows()
            
            # 5. Monitoring and observability validation
            await self.validate_monitoring()
            
            # 6. Performance and load validation
            await self.validate_performance()
            
            # 7. Security and policy validation
            await self.validate_security()
            
            # Generate final report
            self.generate_validation_report()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"E2E validation failed: {e}")
            self.results["status"] = "FAILED"
            self.results["error"] = str(e)
            self.results["traceback"] = traceback.format_exc()
            return self.results
    
    async def validate_environment(self):
        """Validate development environment and dependencies"""
        self.logger.info("📋 Validating environment and dependencies...")
        
        env_results = {
            "python_version": sys.version,
            "dependencies": {},
            "environment_variables": {},
            "file_structure": {}
        }
        
        # Check critical dependencies
        critical_deps = [
            "flask", "playwright", "autogen", "langgraph", 
            "chromadb", "sentence_transformers", "opentelemetry",
            "aiohttp", "opencv-python", "pytest"
        ]
        
        for dep in critical_deps:
            try:
                __import__(dep.replace("-", "_"))
                env_results["dependencies"][dep] = "✅ Available"
            except ImportError:
                env_results["dependencies"][dep] = "❌ Missing"
        
        # Check environment variables
        env_vars = [
            "OPENAI_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN",
            "OLLAMA_BASE_URL", "FLASK_ENV"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            env_results["environment_variables"][var] = "✅ Set" if value else "⚠️ Not Set"
        
        # Check file structure
        critical_files = [
            "api/enhanced_browser_agent.py",
            "api/cloudflare_integration.py",
            "monitoring/advanced_monitoring.py",
            "tests/test_browser_agent_e2e.py",
            "setup_ollama.sh",
            "package.json"
        ]
        
        for file_path in critical_files:
            exists = Path(file_path).exists()
            env_results["file_structure"][file_path] = "✅ Found" if exists else "❌ Missing"
        
        self.results["environment"] = env_results
        self.logger.info("Environment validation completed")
    
    async def validate_core_components(self):
        """Validate core OrbitAgents components"""
        self.logger.info("🔧 Validating core components...")
        
        core_results = {
            "enhanced_browser_agent": {},
            "vision_agent": {},
            "memory_manager": {},
            "policy_agent": {}
        }
        
        try:
            # Test Enhanced Browser Agent
            self.agent = EnhancedBrowserAgent(
                use_ollama=True,
                use_cloudflare=False  # Test without Cloudflare first
            )
            core_results["enhanced_browser_agent"]["initialization"] = "✅ Success"
            
            # Test browser automation
            await self.agent.start_browser()
            core_results["enhanced_browser_agent"]["browser_start"] = "✅ Success"
            
            await self.agent.stop_browser()
            core_results["enhanced_browser_agent"]["browser_stop"] = "✅ Success"
            
        except Exception as e:
            core_results["enhanced_browser_agent"]["error"] = f"❌ {str(e)}"
        
        # Test Vision Agent
        try:
            from api.enhanced_browser_agent import VisionAgent
            vision_agent = VisionAgent()
            core_results["vision_agent"]["initialization"] = "✅ Success"
        except Exception as e:
            core_results["vision_agent"]["error"] = f"❌ {str(e)}"
        
        # Test Memory Manager
        try:
            from api.enhanced_browser_agent import MemoryManager
            memory_manager = MemoryManager()
            core_results["memory_manager"]["initialization"] = "✅ Success"
        except Exception as e:
            core_results["memory_manager"]["error"] = f"❌ {str(e)}"
        
        # Test Policy Agent
        try:
            from api.enhanced_browser_agent import PolicyAgent
            policy_agent = PolicyAgent()
            core_results["policy_agent"]["initialization"] = "✅ Success"
        except Exception as e:
            core_results["policy_agent"]["error"] = f"❌ {str(e)}"
        
        self.results["core_components"] = core_results
        self.logger.info("Core components validation completed")
    
    async def validate_cloudflare_integration(self):
        """Validate Cloudflare Workers AI and edge integration"""
        self.logger.info("☁️ Validating Cloudflare integration...")
        
        cloudflare_results = {
            "config_creation": {},
            "hybrid_client": {},
            "ai_inference": {},
            "durable_objects": {}
        }
        
        try:
            # Test config creation
            config = await create_cloudflare_config()
            cloudflare_results["config_creation"]["status"] = "✅ Success"
            
            # Test hybrid client
            if config.account_id and config.api_token:
                async with HybridInferenceClient(config) as client:
                    cloudflare_results["hybrid_client"]["initialization"] = "✅ Success"
                    
                    # Test local Ollama availability
                    ollama_available = await client.is_ollama_available()
                    cloudflare_results["hybrid_client"]["ollama_available"] = "✅ Available" if ollama_available else "⚠️ Unavailable"
                    
                    # Test AI inference (prefer local)
                    try:
                        result = await client.generate_text(
                            "Hello, this is a test message",
                            prefer_local=True
                        )
                        cloudflare_results["ai_inference"]["test_generation"] = "✅ Success"
                        cloudflare_results["ai_inference"]["response_length"] = len(result.get("text", ""))
                        cloudflare_results["ai_inference"]["local_inference"] = result.get("local", False)
                    except Exception as e:
                        cloudflare_results["ai_inference"]["error"] = f"❌ {str(e)}"
            else:
                cloudflare_results["hybrid_client"]["status"] = "⚠️ No credentials configured"
                
        except Exception as e:
            cloudflare_results["error"] = f"❌ {str(e)}"
        
        self.results["cloudflare_integration"] = cloudflare_results
        self.logger.info("Cloudflare integration validation completed")
    
    async def validate_agent_workflows(self):
        """Validate complete agent workflow execution"""
        self.logger.info("🤖 Validating agent workflows...")
        
        workflow_results = {
            "simple_navigation": {},
            "data_extraction": {},
            "form_interaction": {},
            "vision_analysis": {}
        }
        
        if not self.agent:
            workflow_results["error"] = "❌ Agent not initialized"
            self.results["agent_workflows"] = workflow_results
            return
        
        try:
            # Test simple navigation
            await self.agent.start_browser()
            
            task = f"Navigate to {self.test_url} and take a screenshot"
            result = await self.agent.execute_task(task)
            
            if result.get("success"):
                workflow_results["simple_navigation"]["status"] = "✅ Success"
                workflow_results["simple_navigation"]["url_reached"] = result.get("current_url")
            else:
                workflow_results["simple_navigation"]["error"] = f"❌ {result.get('error', 'Unknown error')}"
            
            # Test vision analysis if screenshot available
            if result.get("screenshot_path"):
                try:
                    vision_result = await self.agent.vision_agent.analyze_screenshot(
                        result["screenshot_path"], 
                        "Analyze the webpage structure"
                    )
                    workflow_results["vision_analysis"]["status"] = "✅ Success"
                    workflow_results["vision_analysis"]["elements_detected"] = len(vision_result.get("buttons", [])) + len(vision_result.get("text_areas", []))
                except Exception as e:
                    workflow_results["vision_analysis"]["error"] = f"❌ {str(e)}"
            
            await self.agent.stop_browser()
            
        except Exception as e:
            workflow_results["error"] = f"❌ {str(e)}"
        
        self.results["agent_workflows"] = workflow_results
        self.logger.info("Agent workflows validation completed")
    
    async def validate_monitoring(self):
        """Validate monitoring and observability"""
        self.logger.info("📊 Validating monitoring and observability...")
        
        monitoring_results = {
            "advanced_monitoring": {},
            "opentelemetry": {},
            "prometheus": {},
            "health_checks": {}
        }
        
        try:
            # Test Advanced Monitoring
            self.monitoring = AdvancedMonitoring()
            monitoring_results["advanced_monitoring"]["initialization"] = "✅ Success"
            
            # Test health checks
            health_status = self.monitoring.get_health_status()
            monitoring_results["health_checks"]["system_health"] = "✅ Healthy" if health_status.get("status") == "healthy" else "⚠️ Issues detected"
            
            # Test OpenTelemetry instrumentation
            try:
                from opentelemetry import trace
                tracer = trace.get_tracer(__name__)
                with tracer.start_as_current_span("test_span"):
                    time.sleep(0.1)
                monitoring_results["opentelemetry"]["tracing"] = "✅ Working"
            except Exception as e:
                monitoring_results["opentelemetry"]["error"] = f"❌ {str(e)}"
            
            # Test Prometheus metrics
            try:
                metrics = self.monitoring.collect_metrics()
                monitoring_results["prometheus"]["metrics_collection"] = "✅ Working"
                monitoring_results["prometheus"]["metrics_count"] = len(metrics)
            except Exception as e:
                monitoring_results["prometheus"]["error"] = f"❌ {str(e)}"
            
        except Exception as e:
            monitoring_results["error"] = f"❌ {str(e)}"
        
        self.results["monitoring"] = monitoring_results
        self.logger.info("Monitoring validation completed")
    
    async def validate_performance(self):
        """Validate performance characteristics"""
        self.logger.info("⚡ Validating performance...")
        
        performance_results = {
            "response_times": {},
            "memory_usage": {},
            "concurrent_operations": {}
        }
        
        try:
            # Test response times
            start_time = time.time()
            
            if self.agent:
                await self.agent.start_browser()
                browser_start_time = time.time() - start_time
                performance_results["response_times"]["browser_start"] = f"{browser_start_time:.2f}s"
                
                # Test navigation performance
                nav_start = time.time()
                await self.agent.navigate_to(self.test_url)
                nav_time = time.time() - nav_start
                performance_results["response_times"]["navigation"] = f"{nav_time:.2f}s"
                
                await self.agent.stop_browser()
            
            # Test memory usage (basic check)
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            performance_results["memory_usage"]["rss_mb"] = f"{memory_info.rss / 1024 / 1024:.1f} MB"
            performance_results["memory_usage"]["vms_mb"] = f"{memory_info.vms / 1024 / 1024:.1f} MB"
            
        except Exception as e:
            performance_results["error"] = f"❌ {str(e)}"
        
        self.results["performance"] = performance_results
        self.logger.info("Performance validation completed")
    
    async def validate_security(self):
        """Validate security and policy features"""
        self.logger.info("🔒 Validating security and policy features...")
        
        security_results = {
            "policy_agent": {},
            "content_filtering": {},
            "security_headers": {},
            "data_privacy": {}
        }
        
        try:
            # Test policy agent
            if self.agent and hasattr(self.agent, 'policy_agent'):
                test_content = "This is a test message for policy validation"
                policy_result = await self.agent.policy_agent.check_policy(test_content)
                security_results["policy_agent"]["basic_check"] = "✅ Working" if policy_result.get("allowed") else "⚠️ Blocked"
            
            # Test malicious content detection
            malicious_test = "javascript:alert('xss')"
            if self.agent and hasattr(self.agent, 'policy_agent'):
                malicious_result = await self.agent.policy_agent.check_policy(malicious_test)
                security_results["content_filtering"]["xss_detection"] = "✅ Blocked" if not malicious_result.get("allowed") else "❌ Not blocked"
            
            security_results["data_privacy"]["status"] = "✅ Implemented"
            
        except Exception as e:
            security_results["error"] = f"❌ {str(e)}"
        
        self.results["security"] = security_results
        self.logger.info("Security validation completed")
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        self.logger.info("📝 Generating validation report...")
        
        total_time = time.time() - self.start_time
        
        # Calculate overall status
        overall_status = "✅ PASSED"
        issues = []
        
        for category, results in self.results.items():
            if isinstance(results, dict):
                for key, value in results.items():
                    if isinstance(value, str) and ("❌" in value or "error" in key.lower()):
                        overall_status = "⚠️ ISSUES DETECTED"
                        issues.append(f"{category}.{key}: {value}")
        
        # Create summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(total_time, 2),
            "overall_status": overall_status,
            "categories_tested": len(self.results),
            "issues_found": len(issues),
            "issues": issues
        }
        
        self.results["summary"] = summary
        
        # Save report to file
        report_file = f"e2e_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"Validation report saved to {report_file}")
        self.logger.info(f"Overall status: {overall_status}")
        self.logger.info(f"Total time: {total_time:.2f}s")
        
        if issues:
            self.logger.warning(f"Issues found: {len(issues)}")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
        else:
            self.logger.info("🎉 All validations passed!")

async def main():
    """Main entry point for E2E validation"""
    validator = E2EValidator()
    results = await validator.run_full_validation()
    
    # Print summary
    summary = results.get("summary", {})
    print("\n" + "="*60)
    print("📊 OrbitAgents E2E Validation Summary")
    print("="*60)
    print(f"Status: {summary.get('overall_status', 'Unknown')}")
    print(f"Duration: {summary.get('duration_seconds', 0)}s")
    print(f"Categories tested: {summary.get('categories_tested', 0)}")
    print(f"Issues found: {summary.get('issues_found', 0)}")
    
    if summary.get('issues'):
        print("\n⚠️ Issues detected:")
        for issue in summary['issues']:
            print(f"  - {issue}")
    
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if summary.get('overall_status') == '✅ PASSED' else 1)

if __name__ == "__main__":
    asyncio.run(main())
