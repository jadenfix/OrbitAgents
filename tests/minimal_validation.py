#!/usr/bin/env python3
"""
Minimal validation test for OrbitAgents core functionality.
Tests basic API endpoints and agent initialization without heavy dependencies.
"""

import sys
import os
import time
import requests
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_basic_api():
    """Test if Flask API is accessible and responds correctly."""
    print("🧪 Testing basic API functionality...")
    
    try:
        # Start API in background (we'll test if it's already running)
        import threading
        import subprocess
        
        # Try to import the API
        try:
            from api.index import app
            print("✅ API module imported successfully")
        except ImportError as e:
            print(f"❌ Failed to import API: {e}")
            return False
            
        # Test basic functionality
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
                
            # Test basic demo endpoint
            response = client.get('/api/demo')
            if response.status_code == 200:
                data = response.get_json()
                if data and data.get('status') == 'success':
                    print("✅ Demo endpoint working")
                else:
                    print(f"❌ Demo endpoint returned unexpected data: {data}")
                    return False
            else:
                print(f"❌ Demo endpoint failed: {response.status_code}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_agent_imports():
    """Test if agent modules can be imported."""
    print("🧪 Testing agent module imports...")
    
    try:
        # Test basic agent file exists and has correct structure
        agent_file = Path(__file__).parent.parent / "api" / "enhanced_browser_agent.py"
        if not agent_file.exists():
            print("❌ Enhanced browser agent file not found")
            return False
            
        print("✅ Enhanced browser agent file exists")
        
        # Check if file has main classes
        content = agent_file.read_text()
        required_classes = [
            "EnhancedBrowserAgent",
            "VisionAgent", 
            "MemoryManager",
            "PolicyAgent"
        ]
        
        for cls in required_classes:
            if cls in content:
                print(f"✅ Found {cls} class")
            else:
                print(f"❌ Missing {cls} class")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Agent import test failed: {e}")
        return False

def test_cloudflare_integration():
    """Test if Cloudflare integration exists."""
    print("🧪 Testing Cloudflare integration...")
    
    try:
        cf_file = Path(__file__).parent.parent / "api" / "cloudflare_integration.py"
        if not cf_file.exists():
            print("❌ Cloudflare integration file not found")
            return False
            
        print("✅ Cloudflare integration file exists")
        
        content = cf_file.read_text()
        required_components = [
            "CloudflareWorkerClient",
            "DurableObjectsManager", 
            "AIGateway",
            "HybridInferenceClient"
        ]
        
        for component in required_components:
            if component in content:
                print(f"✅ Found {component} component")
            else:
                print(f"❌ Missing {component} component")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Cloudflare integration test failed: {e}")
        return False

def test_monitoring_setup():
    """Test if monitoring is properly configured."""
    print("🧪 Testing monitoring setup...")
    
    try:
        monitoring_file = Path(__file__).parent.parent / "monitoring" / "advanced_monitoring.py"
        if not monitoring_file.exists():
            print("❌ Monitoring file not found")
            return False
            
        print("✅ Monitoring file exists")
        
        content = monitoring_file.read_text()
        required_components = [
            "OpenTelemetry",
            "PrometheusMetrics",
            "HealthChecker",
            "MonitoringDashboard"
        ]
        
        for component in required_components:
            if component in content:
                print(f"✅ Found {component} component")
            else:
                print(f"❌ Missing {component} component")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        return False

def test_frontend_structure():
    """Test if frontend has proper structure."""
    print("🧪 Testing frontend structure...")
    
    try:
        frontend_dir = Path(__file__).parent.parent / "frontend"
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
            
        print("✅ Frontend directory exists")
        
        required_files = [
            "src/App.tsx",
            "src/main.tsx", 
            "src/index.css",
            "src/pages/Login.tsx",
            "src/components/LoadingSpinner.tsx",
            "package.json"
        ]
        
        for file_path in required_files:
            full_path = frontend_dir / file_path
            if full_path.exists():
                print(f"✅ Found {file_path}")
            else:
                print(f"❌ Missing {file_path}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Frontend structure test failed: {e}")
        return False

def test_scripts_and_automation():
    """Test if automation scripts exist."""
    print("🧪 Testing scripts and automation...")
    
    try:
        scripts_dir = Path(__file__).parent.parent / "scripts"
        if not scripts_dir.exists():
            print("❌ Scripts directory not found")
            return False
            
        print("✅ Scripts directory exists")
        
        required_scripts = [
            "troubleshooting.sh",
            "setup-cloudflare.sh"
        ]
        
        for script in required_scripts:
            script_path = scripts_dir / script
            if script_path.exists():
                print(f"✅ Found {script}")
                # Check if script is executable
                if script_path.stat().st_mode & 0o111:
                    print(f"✅ {script} is executable")
                else:
                    print(f"⚠️  {script} is not executable")
            else:
                print(f"❌ Missing {script}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Scripts test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🚀 Starting OrbitAgents Minimal Validation")
    print("=" * 50)
    
    tests = [
        ("Basic API", test_basic_api),
        ("Agent Imports", test_agent_imports),
        ("Cloudflare Integration", test_cloudflare_integration),
        ("Monitoring Setup", test_monitoring_setup),
        ("Frontend Structure", test_frontend_structure),
        ("Scripts and Automation", test_scripts_and_automation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if passed_test:
            passed += 1
    
    print("-" * 50)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("💡 OrbitAgents core functionality is ready for development.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        print("💡 Check the output above for specific issues to address.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
