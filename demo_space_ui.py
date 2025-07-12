#!/usr/bin/env python3
"""
Space-Themed Frontend Demo
Showcases the beautiful new OrbitAgents space UI
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def demo_space_frontend():
    print("🌌 OrbitAgents Space UI Demo")
    print("=" * 40)
    
    async with async_playwright() as p:
        # Launch browser in visible mode to see the beautiful UI
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page()
        
        try:
            print("🚀 Loading the space-themed homepage...")
            await page.goto("http://localhost:3002")
            await page.wait_for_load_state('networkidle')
            
            print("✨ Demonstrating beautiful space animations...")
            await asyncio.sleep(5)  # Let animations play
            
            print("🛸 Testing interactive demo button...")
            demo_button = await page.query_selector('button:has-text("Demo Mission")')
            if demo_button:
                await demo_button.click()
                await asyncio.sleep(3)
                
            print("🌍 Testing system health check...")
            health_button = await page.query_selector('button:has-text("System Health Check")')
            if health_button:
                await health_button.click()
                await asyncio.sleep(3)
                
            print("🔐 Navigating to space-themed login page...")
            login_button = await page.query_selector('button:has-text("Sign In")')
            if login_button:
                await login_button.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(5)  # Appreciate the login page design
                
            print("🏠 Returning to home base...")
            home_button = await page.query_selector('button:has-text("Return to Home Base")')
            if home_button:
                await home_button.click()
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
            print("🎯 Testing mobile responsiveness...")
            # Test mobile view
            await page.set_viewport_size({"width": 375, "height": 667})
            await asyncio.sleep(3)
            
            # Back to desktop
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await asyncio.sleep(3)
            
            print("🎉 Demo complete! The space-themed UI is beautiful!")
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
        finally:
            print("🌌 Keeping browser open for exploration...")
            # Don't close browser so user can explore
            input("Press Enter to close browser and end demo...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(demo_space_frontend())
