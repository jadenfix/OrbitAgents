#!/usr/bin/env python3
"""
Quick Integration Test for OrbitAgents Local Development
Tests basic functionality without external dependencies
"""

import sys
import os
import time
import json
from pathlib import Path

def log_info(message):
    print(f"[INFO] {message}")

def log_success(message):
    print(f"[✅] {message}")

def log_error(message):
    print(f"[❌] {message}")

def log_warning(message):
    print(f"[⚠️] {message}")

def test_python_imports():
    """Test critical Python imports"""
    log_info("Testing Python imports...")
    
    imports_to_test = [
        ("flask", "Flask"),
        ("playwright", "Playwright browser automation"),
        ("cv2", "OpenCV computer vision"),
        ("numpy", "NumPy arrays"),
        ("PIL", "Pillow image processing"),
        ("chromadb", "ChromaDB vector database"),
        ("sentence_transformers", "SentenceTransformers embeddings"),
        ("pydantic", "Pydantic data validation"),
        ("structlog", "Structured logging"),
    ]
    
    results = {}
    for module, description in imports_to_test:
        try:
            __import__(module)
            log_success(f"{description}: Available")
            results[module] = True
        except ImportError as e:
            log_error(f"{description}: Missing - {e}")
            results[module] = False
    
    return results

def test_file_structure():
    """Test critical file structure"""
    log_info("Testing file structure...")
    
    critical_files = [
        "api/enhanced_browser_agent.py",
        "api/cloudflare_integration.py",
        "api/requirements.txt",
        "frontend/src/App.tsx",
        "frontend/package.json",
        "package.json",
        "setup.sh",
        "setup_ollama.sh",
        "monitoring/advanced_monitoring.py",
        "tests/test_browser_agent_e2e.py",
        "scripts/troubleshooting.sh",
        "scripts/setup-cloudflare.sh"
    ]
    
    results = {}
    for file_path in critical_files:
        exists = Path(file_path).exists()
        if exists:
            log_success(f"Found: {file_path}")
            results[file_path] = True
        else:
            log_error(f"Missing: {file_path}")
            results[file_path] = False
    
    return results

def test_environment_variables():
    """Test environment variables"""
    log_info("Testing environment variables...")
    
    env_vars = [
        ("NODE_ENV", "Node.js environment"),
        ("FLASK_ENV", "Flask environment"),
        ("PYTHONPATH", "Python path"),
        ("OPENAI_API_KEY", "OpenAI API key (optional)"),
        ("CLOUDFLARE_ACCOUNT_ID", "Cloudflare account (optional)"),
        ("OLLAMA_BASE_URL", "Ollama base URL (optional)")
    ]
    
    results = {}
    for var, description in env_vars:
        value = os.getenv(var)
        if value:
            log_success(f"{description}: Set")
            results[var] = True
        else:
            log_warning(f"{description}: Not set")
            results[var] = False
    
    return results

def test_basic_flask_app():
    """Test basic Flask app functionality"""
    log_info("Testing basic Flask app...")
    
    try:
        # Add API directory to path
        api_path = Path(__file__).parent.parent / "api"
        sys.path.insert(0, str(api_path))
        
        # Try to import the Flask app
        from index import app
        
        # Test basic configuration
        if app:
            log_success("Flask app imported successfully")
            log_success(f"Flask debug mode: {app.debug}")
            return True
        else:
            log_error("Flask app not found")
            return False
            
    except ImportError as e:
        log_error(f"Failed to import Flask app: {e}")
        return False
    except Exception as e:
        log_error(f"Unexpected error testing Flask app: {e}")
        return False

def test_ollama_connection():
    """Test Ollama connection if available"""
    log_info("Testing Ollama connection...")
    
    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Test connection with timeout
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            log_success(f"Ollama connected: {len(models)} models available")
            for model in models[:3]:  # Show first 3 models
                log_info(f"  - {model.get('name', 'Unknown')}")
            return True
        else:
            log_warning(f"Ollama responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        log_warning("Ollama not running or not accessible")
        return False
    except ImportError:
        log_warning("requests module not available for Ollama test")
        return False
    except Exception as e:
        log_warning(f"Ollama test failed: {e}")
        return False

def test_playwright_browsers():
    """Test Playwright browser availability"""
    log_info("Testing Playwright browsers...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Test Chromium
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                log_success("Chromium browser: Available")
                chromium_ok = True
            except Exception as e:
                log_error(f"Chromium browser: Error - {e}")
                chromium_ok = False
            
            # Test Firefox
            try:
                browser = p.firefox.launch(headless=True)
                browser.close()
                log_success("Firefox browser: Available")
                firefox_ok = True
            except Exception as e:
                log_warning(f"Firefox browser: Error - {e}")
                firefox_ok = False
            
            return chromium_ok or firefox_ok
            
    except ImportError:
        log_error("Playwright not available")
        return False
    except Exception as e:
        log_error(f"Playwright test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests"""
    log_info("🚀 Starting OrbitAgents Quick Integration Test")
    log_info("=" * 50)
    
    results = {
        "start_time": time.time(),
        "tests": {}
    }
    
    # Run all tests
    try:
        results["tests"]["python_imports"] = test_python_imports()
        results["tests"]["file_structure"] = test_file_structure()
        results["tests"]["environment_variables"] = test_environment_variables()
        results["tests"]["flask_app"] = test_basic_flask_app()
        results["tests"]["ollama_connection"] = test_ollama_connection()
        results["tests"]["playwright_browsers"] = test_playwright_browsers()
        
    except KeyboardInterrupt:
        log_warning("Tests interrupted by user")
        results["interrupted"] = True
    except Exception as e:
        log_error(f"Unexpected error during tests: {e}")
        results["error"] = str(e)
    
    # Calculate results
    results["end_time"] = time.time()
    results["duration"] = results["end_time"] - results["start_time"]
    
    # Generate summary
    total_tests = 0
    passed_tests = 0
    
    for test_name, test_result in results["tests"].items():
        if isinstance(test_result, bool):
            total_tests += 1
            if test_result:
                passed_tests += 1
        elif isinstance(test_result, dict):
            test_items = len(test_result)
            passed_items = sum(1 for v in test_result.values() if v)
            total_tests += test_items
            passed_tests += passed_items
    
    # Print summary
    log_info("=" * 50)
    log_info("📊 Test Summary")
    log_info(f"Duration: {results['duration']:.2f}s")
    log_info(f"Tests passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        log_success("🎉 All tests passed! Ready for development.")
        status = "PASSED"
    elif passed_tests > total_tests * 0.8:
        log_warning("⚠️ Most tests passed. Some optional features unavailable.")
        status = "MOSTLY_PASSED"
    else:
        log_error("❌ Multiple tests failed. Check setup and dependencies.")
        status = "FAILED"
    
    results["status"] = status
    results["passed_tests"] = passed_tests
    results["total_tests"] = total_tests
    
    # Save results
    report_file = f"integration_test_report_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    log_info(f"Report saved to: {report_file}")
    
    # Provide next steps
    log_info("=" * 50)
    log_info("🚀 Next Steps:")
    log_info("1. Run 'npm run dev' to start the full development environment")
    log_info("2. Check the monitoring dashboard at http://localhost:8000")
    log_info("3. Run E2E tests with 'python tests/e2e_validation_suite.py'")
    log_info("4. Deploy to Cloudflare with './scripts/setup-cloudflare.sh'")
    
    return results

def main():
    """Main entry point"""
    results = run_integration_tests()
    
    # Exit with appropriate code
    if results["status"] == "PASSED":
        sys.exit(0)
    elif results["status"] == "MOSTLY_PASSED":
        sys.exit(0)  # Still allow development
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
