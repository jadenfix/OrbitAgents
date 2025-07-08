"""
Browser Agent Service

A free, open-source browser automation service using Playwright and Puppeteer.
Provides intelligent web automation, form filling, and data extraction capabilities.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import structlog

# Free browser automation tools
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import aioredis
import aiofiles

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# FastAPI app
app = FastAPI(
    title="OrbitAgents Browser Agent Service",
    description="Free browser automation service using Playwright and Puppeteer",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class BrowserAction(BaseModel):
    type: str = Field(..., description="Action type: click, type, scroll, screenshot, etc.")
    selector: Optional[str] = Field(None, description="CSS selector for element")
    text: Optional[str] = Field(None, description="Text to type")
    url: Optional[str] = Field(None, description="URL to navigate to")
    wait_for: Optional[str] = Field(None, description="Element to wait for")
    timeout: int = Field(30000, description="Timeout in milliseconds")

class BrowserTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Task name")
    description: str = Field(..., description="Task description")
    actions: List[BrowserAction] = Field(..., description="List of actions to perform")
    headless: bool = Field(True, description="Run in headless mode")
    browser_type: str = Field("chromium", description="Browser type: chromium, firefox, webkit")
    viewport: Dict[str, int] = Field({"width": 1920, "height": 1080}, description="Viewport size")
    user_agent: Optional[str] = Field(None, description="Custom user agent")

class BrowserTaskResult(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any]
    screenshots: List[str] = []
    logs: List[str] = []
    duration: float
    error: Optional[str] = None

class WebAutomationRequest(BaseModel):
    url: str
    actions: List[Dict[str, Any]]
    options: Dict[str, Any] = {}

class FormFillRequest(BaseModel):
    url: str
    form_data: Dict[str, str]
    submit: bool = False

class ScrapingRequest(BaseModel):
    url: str
    selectors: Dict[str, str]
    wait_for: Optional[str] = None
    scroll_to_bottom: bool = False

# Global browser management
class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browsers: Dict[str, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        self.redis = None
        
    async def initialize(self):
        """Initialize browser management"""
        self.playwright = await async_playwright().start()
        
        # Connect to Redis for task queue
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = await aioredis.from_url(redis_url)
        
        logger.info("Browser manager initialized")
        
    async def get_browser(self, browser_type: str = "chromium", headless: bool = True) -> Browser:
        """Get or create a browser instance"""
        key = f"{browser_type}_{headless}"
        
        if key not in self.browsers:
            browser_launcher = getattr(self.playwright, browser_type)
            self.browsers[key] = await browser_launcher.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-zygote",
                    "--single-process",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ] if headless else []
            )
            
        return self.browsers[key]
        
    async def create_context(self, browser: Browser, viewport: Dict[str, int], user_agent: Optional[str] = None) -> BrowserContext:
        """Create a new browser context"""
        context = await browser.new_context(
            viewport=viewport,
            user_agent=user_agent
        )
        return context
        
    async def close_all(self):
        """Close all browsers and contexts"""
        for browser in self.browsers.values():
            await browser.close()
        self.browsers.clear()
        
        if self.playwright:
            await self.playwright.stop()
            
        if self.redis:
            await self.redis.close()

# Global browser manager instance
browser_manager = BrowserManager()

# Active WebSocket connections
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await browser_manager.initialize()
    
    # Create directories
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    
    logger.info("Browser Agent Service started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await browser_manager.close_all()
    logger.info("Browser Agent Service stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "browser-agent",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/automation/run", response_model=BrowserTaskResult)
async def run_automation_task(task: BrowserTask, background_tasks: BackgroundTasks):
    """Run a browser automation task"""
    logger.info("Starting automation task", task_id=task.id, task_name=task.name)
    
    background_tasks.add_task(execute_browser_task, task)
    
    return BrowserTaskResult(
        task_id=task.id,
        status="queued",
        result={"message": "Task queued for execution"},
        duration=0.0
    )

@app.post("/automation/web-action")
async def perform_web_action(request: WebAutomationRequest):
    """Perform a simple web action"""
    start_time = datetime.utcnow()
    
    try:
        browser = await browser_manager.get_browser("chromium", headless=True)
        context = await browser_manager.create_context(browser, {"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Navigate to URL
        await page.goto(request.url)
        
        results = []
        
        # Execute actions
        for action in request.actions:
            action_type = action.get("type")
            selector = action.get("selector")
            text = action.get("text")
            
            if action_type == "click":
                await page.click(selector)
                results.append({"action": "click", "selector": selector, "status": "success"})
                
            elif action_type == "type":
                await page.fill(selector, text)
                results.append({"action": "type", "selector": selector, "text": text, "status": "success"})
                
            elif action_type == "screenshot":
                screenshot_path = f"screenshots/{uuid.uuid4()}.png"
                await page.screenshot(path=screenshot_path)
                results.append({"action": "screenshot", "path": screenshot_path, "status": "success"})
                
            elif action_type == "wait":
                await page.wait_for_selector(selector, timeout=30000)
                results.append({"action": "wait", "selector": selector, "status": "success"})
                
            elif action_type == "scroll":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                results.append({"action": "scroll", "status": "success"})
        
        await context.close()
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "status": "completed",
            "results": results,
            "duration": duration,
            "url": request.url
        }
        
    except Exception as e:
        logger.error("Web action failed", error=str(e), url=request.url)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation/form-fill")
async def fill_form(request: FormFillRequest):
    """Fill out a form automatically"""
    try:
        browser = await browser_manager.get_browser("chromium", headless=True)
        context = await browser_manager.create_context(browser, {"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Navigate to URL
        await page.goto(request.url)
        
        # Fill form fields
        for field_name, value in request.form_data.items():
            # Try multiple selector strategies
            selectors = [
                f'input[name="{field_name}"]',
                f'input[id="{field_name}"]',
                f'textarea[name="{field_name}"]',
                f'select[name="{field_name}"]'
            ]
            
            for selector in selectors:
                try:
                    await page.fill(selector, value)
                    break
                except:
                    continue
        
        # Submit form if requested
        if request.submit:
            await page.click('button[type="submit"], input[type="submit"]')
            await page.wait_for_load_state("networkidle")
        
        # Take screenshot
        screenshot_path = f"screenshots/form_fill_{uuid.uuid4()}.png"
        await page.screenshot(path=screenshot_path)
        
        await context.close()
        
        return {
            "status": "completed",
            "form_data": request.form_data,
            "submitted": request.submit,
            "screenshot": screenshot_path
        }
        
    except Exception as e:
        logger.error("Form fill failed", error=str(e), url=request.url)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/automation/scrape")
async def scrape_data(request: ScrapingRequest):
    """Scrape data from a webpage"""
    try:
        browser = await browser_manager.get_browser("chromium", headless=True)
        context = await browser_manager.create_context(browser, {"width": 1920, "height": 1080})
        page = await context.new_page()
        
        # Navigate to URL
        await page.goto(request.url)
        
        # Wait for specific element if specified
        if request.wait_for:
            await page.wait_for_selector(request.wait_for, timeout=30000)
        
        # Scroll to bottom if requested
        if request.scroll_to_bottom:
            await page.evaluate("""
                async () => {
                    await new Promise((resolve) => {
                        let totalHeight = 0;
                        let distance = 100;
                        let timer = setInterval(() => {
                            let scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
        
        # Extract data using selectors
        scraped_data = {}
        for key, selector in request.selectors.items():
            try:
                elements = await page.query_selector_all(selector)
                if len(elements) == 1:
                    scraped_data[key] = await elements[0].text_content()
                else:
                    scraped_data[key] = [await elem.text_content() for elem in elements]
            except Exception as e:
                scraped_data[key] = f"Error: {str(e)}"
        
        await context.close()
        
        return {
            "status": "completed",
            "url": request.url,
            "data": scraped_data
        }
        
    except Exception as e:
        logger.error("Scraping failed", error=str(e), url=request.url)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Get a screenshot file"""
    file_path = f"screenshots/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="Screenshot not found")

@app.websocket("/ws/automation")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time automation updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now - can be extended for real-time control
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def execute_browser_task(task: BrowserTask):
    """Execute a browser automation task in the background"""
    start_time = datetime.utcnow()
    
    try:
        browser = await browser_manager.get_browser(task.browser_type, task.headless)
        context = await browser_manager.create_context(browser, task.viewport, task.user_agent)
        page = await context.new_page()
        
        results = []
        screenshots = []
        logs = []
        
        # Execute each action
        for action in task.actions:
            action_start = datetime.utcnow()
            
            try:
                if action.type == "navigate":
                    await page.goto(action.url)
                    
                elif action.type == "click":
                    await page.click(action.selector)
                    
                elif action.type == "type":
                    await page.fill(action.selector, action.text)
                    
                elif action.type == "screenshot":
                    screenshot_path = f"screenshots/{task.id}_{len(screenshots)}.png"
                    await page.screenshot(path=screenshot_path)
                    screenshots.append(screenshot_path)
                    
                elif action.type == "wait":
                    await page.wait_for_selector(action.selector, timeout=action.timeout)
                    
                elif action.type == "scroll":
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                action_duration = (datetime.utcnow() - action_start).total_seconds()
                results.append({
                    "action": action.type,
                    "status": "success",
                    "duration": action_duration
                })
                
            except Exception as e:
                results.append({
                    "action": action.type,
                    "status": "failed",
                    "error": str(e)
                })
                logs.append(f"Action {action.type} failed: {str(e)}")
        
        await context.close()
        
        # Save results to Redis
        task_result = BrowserTaskResult(
            task_id=task.id,
            status="completed",
            result={"actions": results},
            screenshots=screenshots,
            logs=logs,
            duration=(datetime.utcnow() - start_time).total_seconds()
        )
        
        await browser_manager.redis.setex(
            f"task_result:{task.id}",
            3600,  # 1 hour TTL
            task_result.json()
        )
        
        # Notify WebSocket clients
        for connection in active_connections:
            try:
                await connection.send_text(f"Task {task.id} completed")
            except:
                pass
        
        logger.info("Browser task completed", task_id=task.id, duration=task_result.duration)
        
    except Exception as e:
        logger.error("Browser task failed", task_id=task.id, error=str(e))
        
        # Save error result
        error_result = BrowserTaskResult(
            task_id=task.id,
            status="failed",
            result={},
            duration=(datetime.utcnow() - start_time).total_seconds(),
            error=str(e)
        )
        
        await browser_manager.redis.setex(
            f"task_result:{task.id}",
            3600,
            error_result.json()
        )

@app.get("/tasks/{task_id}/result", response_model=BrowserTaskResult)
async def get_task_result(task_id: str):
    """Get the result of a browser automation task"""
    result = await browser_manager.redis.get(f"task_result:{task_id}")
    
    if not result:
        raise HTTPException(status_code=404, detail="Task result not found")
    
    return BrowserTaskResult.parse_raw(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
