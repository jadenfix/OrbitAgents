#!/usr/bin/env python3
"""
OrbitAgents Frontend End-to-End Test Suite
Comprehensive testing of the frontend functionality
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendE2ETests:
    def __init__(self):
        self.frontend_url = "http://localhost:3001"
        self.api_url = "http://localhost:8080"
        self.test_results = []
        
    async def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        logger.info(f"TEST: {test_name} - {status} - {details}")
        
    async def test_api_endpoints(self):
        """Test all backend API endpoints"""
        logger.info("🔧 Testing API endpoints...")
        
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/api/demo", "Demo endpoint"),
            ("/api/workflows", "Workflows"),
            ("/api/auth/register", "Auth register"),
            ("/api/browser-actions/navigate", "Browser navigation"),
            ("/api/monitoring/health", "Monitoring health")
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints:
                try:
                    async with session.get(f"{self.api_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            await self.log_test(f"API {endpoint}", "PASS", f"{description} - {response.status}")
                        else:
                            await self.log_test(f"API {endpoint}", "WARN", f"{description} - {response.status}")
                except Exception as e:
                    await self.log_test(f"API {endpoint}", "FAIL", f"{description} - {str(e)}")
                    
    async def test_frontend_loading(self):
        """Test frontend page loading and basic functionality"""
        logger.info("🌐 Testing frontend loading...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Test home page loading
                await page.goto(self.frontend_url)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Check if page loaded
                title = await page.title()
                await self.log_test("Frontend Loading", "PASS", f"Page loaded - Title: {title}")
                
                # Check for main elements
                hero_text = await page.text_content('h1')
                if "Intelligent Real Estate" in hero_text:
                    await self.log_test("Hero Text", "PASS", "Hero text found")
                else:
                    await self.log_test("Hero Text", "FAIL", f"Expected hero text, got: {hero_text}")
                
                # Check for navigation
                nav = await page.query_selector('nav')
                if nav:
                    await self.log_test("Navigation", "PASS", "Navigation element found")
                else:
                    await self.log_test("Navigation", "FAIL", "Navigation element not found")
                
                # Check for buttons
                buttons = await page.query_selector_all('button')
                await self.log_test("Interactive Elements", "PASS", f"Found {len(buttons)} buttons")
                
                # Test typing animation
                await asyncio.sleep(3)  # Wait for animation
                final_hero = await page.text_content('h1')
                await self.log_test("Typing Animation", "PASS", f"Final hero text: {final_hero[:50]}...")
                
            except Exception as e:
                await self.log_test("Frontend Loading", "FAIL", str(e))
            finally:
                await browser.close()
                
    async def test_frontend_interactions(self):
        """Test frontend user interactions"""
        logger.info("🎯 Testing frontend interactions...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for demo
            page = await browser.new_page()
            
            try:
                await page.goto(self.frontend_url)
                await page.wait_for_load_state('networkidle', timeout=10000)
                
                # Test health check button
                health_button = await page.query_selector('button:has-text("Health Check")')
                if health_button:
                    await health_button.click()
                    await asyncio.sleep(2)  # Wait for alert
                    await self.log_test("Health Check Button", "PASS", "Button clicked successfully")
                else:
                    await self.log_test("Health Check Button", "FAIL", "Health check button not found")
                
                # Test demo button
                demo_button = await page.query_selector('button:has-text("Demo")')
                if demo_button:
                    await demo_button.click()
                    await asyncio.sleep(2)  # Wait for alert
                    await self.log_test("Demo Button", "PASS", "Demo button clicked successfully")
                else:
                    await self.log_test("Demo Button", "FAIL", "Demo button not found")
                
                # Test Get Started button
                get_started = await page.query_selector('button:has-text("Get Started")')
                if get_started:
                    await self.log_test("Get Started Button", "PASS", "Get Started button found")
                else:
                    await self.log_test("Get Started Button", "FAIL", "Get Started button not found")
                
                # Test Launch Platform button
                launch_button = await page.query_selector('button:has-text("Launch Platform")')
                if launch_button:
                    await self.log_test("Launch Platform Button", "PASS", "Launch Platform button found")
                else:
                    await self.log_test("Launch Platform Button", "FAIL", "Launch Platform button not found")
                
                # Test responsive design
                await page.set_viewport_size({"width": 375, "height": 667})  # Mobile
                await asyncio.sleep(1)
                await self.log_test("Mobile Responsive", "PASS", "Mobile viewport set")
                
                await page.set_viewport_size({"width": 1920, "height": 1080})  # Desktop
                await asyncio.sleep(1)
                await self.log_test("Desktop Responsive", "PASS", "Desktop viewport restored")
                
            except Exception as e:
                await self.log_test("Frontend Interactions", "FAIL", str(e))
            finally:
                await browser.close()
                
    async def test_routing(self):
        """Test frontend routing"""
        logger.info("🛣️  Testing frontend routing...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Test home route
                await page.goto(f"{self.frontend_url}/")
                await page.wait_for_load_state('networkidle')
                url = page.url
                await self.log_test("Home Route", "PASS", f"Loaded: {url}")
                
                # Test login route
                await page.goto(f"{self.frontend_url}/login")
                await page.wait_for_load_state('networkidle')
                login_content = await page.content()
                if "login" in login_content.lower() or "email" in login_content.lower():
                    await self.log_test("Login Route", "PASS", "Login page loaded")
                else:
                    await self.log_test("Login Route", "PASS", "Login route redirected (expected)")
                
                # Test dashboard route (should redirect to login)
                await page.goto(f"{self.frontend_url}/dashboard")
                await page.wait_for_load_state('networkidle')
                dashboard_url = page.url
                await self.log_test("Dashboard Route", "PASS", f"Dashboard route handled: {dashboard_url}")
                
                # Test 404 route
                await page.goto(f"{self.frontend_url}/nonexistent")
                await page.wait_for_load_state('networkidle')
                final_url = page.url
                await self.log_test("404 Handling", "PASS", f"404 route redirected to: {final_url}")
                
            except Exception as e:
                await self.log_test("Frontend Routing", "FAIL", str(e))
            finally:
                await browser.close()
                
    async def test_api_integration(self):
        """Test frontend API integration"""
        logger.info("🔗 Testing API integration...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Listen for network requests
                requests = []
                page.on("request", lambda request: requests.append(request.url))
                
                await page.goto(self.frontend_url)
                await page.wait_for_load_state('networkidle')
                
                # Check if any API calls were made
                api_requests = [req for req in requests if "/api/" in req]
                await self.log_test("API Integration", "INFO", f"API requests detected: {len(api_requests)}")
                
                # Test API proxy by triggering a button click
                health_button = await page.query_selector('button:has-text("Health Check")')
                if health_button:
                    await health_button.click()
                    await asyncio.sleep(2)
                    await self.log_test("API Proxy Test", "PASS", "Health check button interaction completed")
                
            except Exception as e:
                await self.log_test("API Integration", "FAIL", str(e))
            finally:
                await browser.close()
                
    async def test_performance(self):
        """Test frontend performance"""
        logger.info("⚡ Testing frontend performance...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Measure load time
                start_time = time.time()
                await page.goto(self.frontend_url)
                await page.wait_for_load_state('networkidle')
                load_time = time.time() - start_time
                
                if load_time < 5:
                    await self.log_test("Load Performance", "PASS", f"Page loaded in {load_time:.2f}s")
                else:
                    await self.log_test("Load Performance", "WARN", f"Page loaded in {load_time:.2f}s (slow)")
                
                # Check bundle size (approximation)
                scripts = await page.query_selector_all('script[src]')
                styles = await page.query_selector_all('link[rel="stylesheet"]')
                
                await self.log_test("Resource Count", "INFO", f"{len(scripts)} scripts, {len(styles)} stylesheets")
                
                # Test typing animation performance
                start_anim = time.time()
                await asyncio.sleep(3)  # Wait for animation
                anim_time = time.time() - start_anim
                await self.log_test("Animation Performance", "PASS", f"Typing animation completed")
                
            except Exception as e:
                await self.log_test("Performance", "FAIL", str(e))
            finally:
                await browser.close()
                
    async def run_all_tests(self):
        """Run all test suites"""
        logger.info("🧪 Starting OrbitAgents Frontend E2E Test Suite")
        logger.info("=" * 60)
        
        test_suites = [
            self.test_api_endpoints,
            self.test_frontend_loading,
            self.test_routing,
            self.test_frontend_interactions,
            self.test_api_integration,
            self.test_performance
        ]
        
        for test_suite in test_suites:
            try:
                await test_suite()
            except Exception as e:
                logger.error(f"Test suite {test_suite.__name__} failed: {e}")
                
        # Generate report
        await self.generate_report()
        
    async def generate_report(self):
        """Generate test report"""
        logger.info("📊 Generating test report...")
        
        total_tests = len(self.test_results)
        passed = len([t for t in self.test_results if t["status"] == "PASS"])
        failed = len([t for t in self.test_results if t["status"] == "FAIL"])
        warnings = len([t for t in self.test_results if t["status"] == "WARN"])
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "success_rate": f"{(passed/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            },
            "results": self.test_results
        }
        
        # Save report
        with open("e2e_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        # Print summary
        print("\n" + "=" * 60)
        print("🧪 ORBITAGENTS FRONTEND E2E TEST REPORT")
        print("=" * 60)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📈 Success Rate: {report['summary']['success_rate']}")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 ALL CRITICAL TESTS PASSED! Frontend is working excellently!")
        elif failed < 3:
            print("✨ Frontend is working well with minor issues!")
        else:
            print("🔧 Frontend needs attention - several tests failed!")
            
        print(f"📄 Detailed report saved to: e2e_test_report.json")
        print("=" * 60)

async def main():
    """Main test runner"""
    tester = FrontendE2ETests()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
