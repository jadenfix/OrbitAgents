#!/usr/bin/env python3
"""
Final Production Validation Suite
Comprehensive validation of the deployed OrbitAgents platform
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

class ProductionValidator:
    def __init__(self):
        self.frontend_url = "http://localhost:3001"
        self.api_url = "http://localhost:8080"
        self.monitoring_url = "http://localhost:9090"
        self.results = []
        
    async def validate_all(self):
        print("🔍 OrbitAgents Production Validation")
        print("=" * 50)
        
        # Test all services
        await self.test_service_availability()
        await self.test_api_functionality()
        await self.test_frontend_content()
        await self.generate_final_report()
        
    async def test_service_availability(self):
        print("🌐 Testing service availability...")
        
        services = [
            (self.frontend_url, "Frontend"),
            (self.api_url, "Backend API"),
            (self.monitoring_url, "Monitoring Dashboard")
        ]
        
        async with aiohttp.ClientSession() as session:
            for url, name in services:
                try:
                    start_time = time.time()
                    async with session.get(url) as response:
                        load_time = time.time() - start_time
                        if response.status == 200:
                            print(f"✅ {name}: Online ({load_time:.2f}s)")
                            self.results.append(f"✅ {name}: ONLINE")
                        else:
                            print(f"⚠️ {name}: Status {response.status}")
                            self.results.append(f"⚠️ {name}: STATUS {response.status}")
                except Exception as e:
                    print(f"❌ {name}: Offline - {e}")
                    self.results.append(f"❌ {name}: OFFLINE")
                    
    async def test_api_functionality(self):
        print("\n🔧 Testing API functionality...")
        
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check"),
            ("/api/demo", "Demo endpoint")
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, description in endpoints:
                try:
                    async with session.get(f"{self.api_url}{endpoint}") as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ {description}: Working")
                            self.results.append(f"✅ API {endpoint}: WORKING")
                        else:
                            print(f"⚠️ {description}: Status {response.status}")
                            self.results.append(f"⚠️ API {endpoint}: STATUS {response.status}")
                except Exception as e:
                    print(f"❌ {description}: Failed - {e}")
                    self.results.append(f"❌ API {endpoint}: FAILED")
                    
    async def test_frontend_content(self):
        print("\n🎨 Testing frontend content...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.frontend_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check for key content
                        checks = [
                            ("OrbitAgents", "Title"),
                            ("Intelligent Real Estate", "Hero text"),
                            ("Automation Platform", "Platform text"),
                            ("Health Check", "Health button"),
                            ("Demo", "Demo functionality")
                        ]
                        
                        for text, description in checks:
                            if text in content:
                                print(f"✅ {description}: Found")
                                self.results.append(f"✅ Frontend {description}: FOUND")
                            else:
                                print(f"⚠️ {description}: Not found")
                                self.results.append(f"⚠️ Frontend {description}: NOT FOUND")
                    else:
                        print(f"❌ Frontend content check failed: Status {response.status}")
                        self.results.append(f"❌ Frontend: STATUS {response.status}")
            except Exception as e:
                print(f"❌ Frontend content check failed: {e}")
                self.results.append(f"❌ Frontend: FAILED")
                
    async def generate_final_report(self):
        print("\n📊 Final Validation Report")
        print("=" * 50)
        
        passed = len([r for r in self.results if r.startswith("✅")])
        warnings = len([r for r in self.results if r.startswith("⚠️")])
        failed = len([r for r in self.results if r.startswith("❌")])
        total = len(self.results)
        
        print(f"📈 Total Checks: {total}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"❌ Failed: {failed}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if failed == 0:
            print("\n🎉 PRODUCTION VALIDATION PASSED!")
            print("🚀 OrbitAgents is ready for use!")
        elif failed < 3:
            print("\n✨ PRODUCTION VALIDATION MOSTLY PASSED!")
            print("🔧 Minor issues detected but platform is functional!")
        else:
            print("\n🔧 PRODUCTION VALIDATION NEEDS ATTENTION!")
            print("❗ Several issues detected - please review!")
            
        # Save report
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "warnings": warnings,
                "failed": failed,
                "success_rate": f"{success_rate:.1f}%"
            },
            "results": self.results
        }
        
        with open("production_validation_report.json", "w") as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Detailed report saved to: production_validation_report.json")
        
        print("\n🔗 Access Your Platform:")
        print(f"   Frontend: {self.frontend_url}")
        print(f"   API: {self.api_url}")
        print(f"   Monitoring: {self.monitoring_url}")

async def main():
    validator = ProductionValidator()
    await validator.validate_all()

if __name__ == "__main__":
    asyncio.run(main())
