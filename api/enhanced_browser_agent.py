"""
AutoGen + LangGraph Enhanced Browser Agent
Implements the 1000x better AI browser agent architecture with:
- Vision-capable browser automation
- Advanced planning and reflection loops
- Long-term memory with vector storage
- Policy guardrails and self-healing
- Continuous learning capabilities
"""

import asyncio
import json
import logging
import os
import time
import uuid
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import base64
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
from collections import defaultdict

# AutoGen & LangGraph
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.messages import BaseMessage

# Browser Automation & Vision
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import cv2
import numpy as np
from PIL import Image
import pytesseract

# AI & Embeddings
import openai
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Utilities & Monitoring
from pydantic import BaseModel, Field
import structlog
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Cloudflare Integration
from cloudflare_integration import (
    CloudflareConfig, 
    CloudflareAIClient, 
    DurableObjectsClient, 
    HybridInferenceClient,
    create_cloudflare_config
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
import requests

# Configure OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

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

logger = structlog.get_logger()

@dataclass
class AgentState:
    """State management for the browser agent"""
    current_url: str = ""
    task_description: str = ""
    extracted_data: Dict[str, Any] = None
    screenshots: List[str] = None
    error_log: List[str] = None
    memory: Dict[str, Any] = None
    plan: List[Dict[str, Any]] = None
    current_step: int = 0
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}
        if self.screenshots is None:
            self.screenshots = []
        if self.error_log is None:
            self.error_log = []
        if self.memory is None:
            self.memory = {}
        if self.plan is None:
            self.plan = []

class VisionAgent:
    """AI Vision agent for element detection and analysis"""
    
    def __init__(self):
        self.logger = logger.bind(component="vision_agent")
    
    async def analyze_screenshot(self, screenshot_path: str, task: str) -> Dict[str, Any]:
        """Analyze screenshot using computer vision and AI"""
        try:
            # Load and process image
            image = cv2.imread(screenshot_path)
            
            # Convert to different formats for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect UI elements using computer vision
            buttons = self._detect_buttons(gray)
            text_areas = self._detect_text_areas(gray)
            forms = self._detect_forms(gray)
            
            analysis = {
                "buttons": buttons,
                "text_areas": text_areas,
                "forms": forms,
                "dimensions": {"width": image.shape[1], "height": image.shape[0]},
                "task_relevance": self._analyze_task_relevance(task, buttons, text_areas, forms)
            }
            
            self.logger.info("Screenshot analyzed", 
                           elements_found=len(buttons) + len(text_areas) + len(forms))
            
            return analysis
            
        except Exception as e:
            self.logger.error("Screenshot analysis failed", error=str(e))
            return {"error": str(e)}
    
    def _detect_buttons(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect button-like elements in the image"""
        # Use edge detection and contour finding
        edges = cv2.Canny(gray_image, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        buttons = []
        for contour in contours:
            # Filter contours by area and aspect ratio to find button-like shapes
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum button size
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.2 < aspect_ratio < 5:  # Reasonable aspect ratio for buttons
                    buttons.append({
                        "type": "button",
                        "bbox": {"x": x, "y": y, "width": w, "height": h},
                        "area": area,
                        "confidence": 0.7
                    })
        
        return buttons[:10]  # Limit to top 10 candidates
    
    def _detect_text_areas(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect text areas using OCR"""
        try:
            # Use pytesseract to detect text regions
            data = pytesseract.image_to_data(gray_image, output_type=pytesseract.Output.DICT)
            
            text_areas = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 30:  # Confidence threshold
                    text = data['text'][i].strip()
                    if text:  # Non-empty text
                        text_areas.append({
                            "type": "text",
                            "text": text,
                            "bbox": {
                                "x": data['left'][i],
                                "y": data['top'][i],
                                "width": data['width'][i],
                                "height": data['height'][i]
                            },
                            "confidence": data['conf'][i] / 100.0
                        })
            
            return text_areas[:20]  # Limit to top 20 text areas
            
        except Exception as e:
            self.logger.warning("OCR detection failed", error=str(e))
            return []
    
    def _detect_forms(self, gray_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect form-like structures"""
        # Simple form detection based on rectangular shapes
        contours, _ = cv2.findContours(gray_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        forms = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 2000:  # Minimum form size
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 3:  # Form-like aspect ratio
                    forms.append({
                        "type": "form",
                        "bbox": {"x": x, "y": y, "width": w, "height": h},
                        "area": area,
                        "confidence": 0.6
                    })
        
        return forms[:5]  # Limit to top 5 form candidates
    
    def _analyze_task_relevance(self, task: str, buttons: List, text_areas: List, forms: List) -> Dict[str, float]:
        """Analyze how relevant detected elements are to the task"""
        task_lower = task.lower()
        relevance = {
            "buttons": 0.0,
            "text_areas": 0.0,
            "forms": 0.0
        }
        
        # Simple keyword-based relevance scoring
        if any(keyword in task_lower for keyword in ["click", "button", "submit", "login"]):
            relevance["buttons"] = 0.9
        if any(keyword in task_lower for keyword in ["read", "text", "content", "extract"]):
            relevance["text_areas"] = 0.9
        if any(keyword in task_lower for keyword in ["form", "fill", "input", "register"]):
            relevance["forms"] = 0.9
        
        return relevance


class MemoryManager:
    """Advanced memory management with vector storage"""
    
    def __init__(self, collection_name: str = "browser_agent_memory"):
        self.logger = logger.bind(component="memory_manager")
        self.collection_name = collection_name
        self._init_chroma()
        self._init_sentence_transformer()
    
    def _init_chroma(self):
        """Initialize ChromaDB for vector storage"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
            
            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(name=self.collection_name)
                self.logger.info("Connected to existing ChromaDB collection")
            except:
                self.collection = self.chroma_client.create_collection(name=self.collection_name)
                self.logger.info("Created new ChromaDB collection")
                
        except Exception as e:
            self.logger.error("ChromaDB initialization failed", error=str(e))
            self.collection = None
    
    def _init_sentence_transformer(self):
        """Initialize sentence transformer for embeddings"""
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            self.logger.info("Sentence transformer initialized")
        except Exception as e:
            self.logger.error("Sentence transformer initialization failed", error=str(e))
            self.encoder = None
    
    async def store_experience(self, action: str, context: str, result: str, url: str):
        """Store browsing experience in vector memory"""
        if not self.collection or not self.encoder:
            return
        
        try:
            # Create document text
            doc_text = f"Action: {action}\nContext: {context}\nResult: {result}\nURL: {url}"
            
            # Generate embedding
            embedding = self.encoder.encode([doc_text])[0].tolist()
            
            # Store in ChromaDB
            doc_id = f"{uuid.uuid4()}"
            self.collection.add(
                documents=[doc_text],
                embeddings=[embedding],
                metadatas=[{
                    "action": action,
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "type": "experience"
                }],
                ids=[doc_id]
            )
            
            self.logger.info("Experience stored", action=action, url=url)
            
        except Exception as e:
            self.logger.error("Failed to store experience", error=str(e))
    
    async def retrieve_similar_experiences(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve similar past experiences"""
        if not self.collection or not self.encoder:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.encoder.encode([query])[0].tolist()
            
            # Search similar experiences
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            experiences = []
            for i, doc in enumerate(results['documents'][0]):
                experiences.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results else 0.0
                })
            
            self.logger.info("Retrieved experiences", count=len(experiences))
            return experiences
            
        except Exception as e:
            self.logger.error("Failed to retrieve experiences", error=str(e))
            return []


class PolicyAgent:
    """Policy and safety guardrails for browser actions"""
    
    def __init__(self):
        self.logger = logger.bind(component="policy_agent")
        self.blocked_domains = ["malware.com", "phishing.com"]  # Example blocked domains
        self.sensitive_actions = ["delete", "purchase", "payment", "submit_form"]
    
    async def validate_action(self, action: str, url: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if an action is safe and allowed"""
        try:
            # Check domain blacklist
            domain = urlparse(url).netloc
            if domain in self.blocked_domains:
                return False, f"Domain {domain} is blocked"
            
            # Check for sensitive actions
            if any(sensitive in action.lower() for sensitive in self.sensitive_actions):
                if not self._validate_sensitive_action(action, context):
                    return False, f"Sensitive action {action} requires additional validation"
            
            # Check for potential security risks
            if self._contains_security_risk(action, context):
                return False, "Action contains potential security risks"
            
            self.logger.info("Action validated", action=action, url=url)
            return True, "Action approved"
            
        except Exception as e:
            self.logger.error("Action validation failed", error=str(e))
            return False, f"Validation error: {str(e)}"
    
    def _validate_sensitive_action(self, action: str, context: Dict[str, Any]) -> bool:
        """Validate sensitive actions with additional checks"""
        # Implement specific validation logic for sensitive actions
        # For now, require explicit user confirmation for sensitive actions
        return context.get("user_confirmed", False)
    
    def _contains_security_risk(self, action: str, context: Dict[str, Any]) -> bool:
        """Check for potential security risks in actions"""
        risk_patterns = [
            "eval(",
            "javascript:",
            "data:text/html",
            "file://",
            "chrome://",
            "about:"
        ]
        
        action_lower = action.lower()
        return any(pattern in action_lower for pattern in risk_patterns)


class OllamaClient:
    """Client for local Ollama inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.logger = logger.bind(component="ollama_client")
    
    async def generate(self, model: str, prompt: str, **kwargs) -> str:
        """Generate text using Ollama model"""
        try:
            import aiohttp
            
            data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                **kwargs
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "")
                    else:
                        self.logger.error("Ollama request failed", status=response.status)
                        return ""
                        
        except Exception as e:
            self.logger.error("Ollama generation failed", error=str(e))
            return ""
    
    async def check_health(self) -> bool:
        """Check if Ollama server is running"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
                    
        except Exception:
            return False


class EnhancedBrowserAgent:
    """
    1000x better AI browser agent with:
    - Vision-capable browser automation
    - Advanced planning and reflection loops
    - Long-term memory with vector storage
    - Policy guardrails and self-healing
    - Continuous learning capabilities
    """
    
    def __init__(self, 
                 use_ollama: bool = True,
                 ollama_model: str = "mixtral:8x22b",
                 openai_api_key: Optional[str] = None,
                 use_cloudflare: bool = True,
                 cloudflare_config: Optional[CloudflareConfig] = None):
        
        self.logger = logger.bind(component="enhanced_browser_agent")
        
        # Initialize components
        self.vision_agent = VisionAgent()
        self.memory_manager = MemoryManager()
        self.policy_agent = PolicyAgent()
        self.ollama_client = OllamaClient() if use_ollama else None
        self.ollama_model = ollama_model
        
        # Cloudflare integration
        self.use_cloudflare = use_cloudflare
        self.cloudflare_config = cloudflare_config
        self.hybrid_client: Optional[HybridInferenceClient] = None
        self.durable_objects_client: Optional[DurableObjectsClient] = None
        
        # Browser state
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # OpenAI fallback
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Initialize Cloudflare clients if enabled
        if self.use_cloudflare and self.cloudflare_config:
            self._init_cloudflare_clients()
        
        # Initialize AutoGen agents
        self._init_autogen_agents()
        
        # Initialize LangGraph workflow
        self._init_langgraph_workflow()
    
    def _init_autogen_agents(self):
        """Initialize AutoGen multi-agent system"""
        try:
            # Main planning agent
            self.planner_agent = AssistantAgent(
                name="planner",
                system_message="""You are an expert web automation planner. 
                Analyze tasks and create detailed step-by-step plans for browser automation.
                Consider user intent, website structure, and potential challenges.
                Always prioritize safety and user privacy.""",
                llm_config={
                    "config_list": [{"model": "gpt-4", "api_key": openai.api_key}] if openai.api_key else [],
                    "temperature": 0.1
                }
            )
            
            # Browser execution agent
            self.executor_agent = AssistantAgent(
                name="executor",
                system_message="""You are a browser automation executor. 
                Execute browser actions based on plans from the planner.
                Use vision analysis to interact with web elements.
                Report results and handle errors gracefully.""",
                llm_config={
                    "config_list": [{"model": "gpt-4", "api_key": openai.api_key}] if openai.api_key else [],
                    "temperature": 0.1
                }
            )
            
            # Reflection and quality agent
            self.reflector_agent = AssistantAgent(
                name="reflector",
                system_message="""You are a quality assurance agent for web automation.
                Review executed actions and their results.
                Identify issues, suggest improvements, and ensure task completion.
                Learn from mistakes to improve future performance.""",
                llm_config={
                    "config_list": [{"model": "gpt-4", "api_key": openai.api_key}] if openai.api_key else [],
                    "temperature": 0.1
                }
            )
            
            # User proxy for interaction
            self.user_proxy = UserProxyAgent(
                name="user_proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                code_execution_config=False
            )
            
            self.logger.info("AutoGen agents initialized")
            
        except Exception as e:
            self.logger.error("AutoGen initialization failed", error=str(e))
            # Fallback to simple agents
            self.planner_agent = None
            self.executor_agent = None
            self.reflector_agent = None
            self.user_proxy = None
    
    def _init_langgraph_workflow(self):
        """Initialize LangGraph workflow for orchestration"""
        try:
            from langgraph.graph import StateGraph, END, START
            from langgraph.checkpoint.memory import MemorySaver
            
            # Define workflow state
            workflow = StateGraph(AgentState)
            
            # Add workflow nodes
            workflow.add_node("plan", self._plan_node)
            workflow.add_node("execute", self._execute_node)
            workflow.add_node("reflect", self._reflect_node)
            workflow.add_node("memory_store", self._memory_store_node)
            
            # Define workflow edges
            workflow.add_edge(START, "plan")
            workflow.add_edge("plan", "execute")
            workflow.add_edge("execute", "reflect")
            workflow.add_conditional_edges(
                "reflect",
                self._should_continue,
                {
                    "continue": "execute",
                    "memory": "memory_store",
                    "end": END
                }
            )
            workflow.add_edge("memory_store", END)
            
            # Add memory checkpointer
            memory = MemorySaver()
            self.workflow = workflow.compile(checkpointer=memory)
            
            self.logger.info("LangGraph workflow initialized")
            
        except Exception as e:
            self.logger.error("LangGraph workflow initialization failed", error=str(e))
            self.workflow = None
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Planning node in the LangGraph workflow"""
        try:
            # Use Ollama or OpenAI for planning
            if self.ollama_client and await self.ollama_client.check_health():
                planning_prompt = f"""
                Task: {state.task_description}
                Current URL: {state.current_url}
                
                Create a detailed step-by-step plan for this browser automation task.
                Consider the current context and any previous errors.
                
                Format your response as a JSON list of steps with these fields:
                - action: The action to perform
                - element: Target element description
                - value: Any value to input (if applicable)
                - expected_result: What should happen
                
                Previous errors: {state.error_log[-3:] if state.error_log else 'None'}
                """
                
                response = await self.ollama_client.generate(
                    model=self.ollama_model,
                    prompt=planning_prompt
                )
                
                # Parse response into plan steps
                try:
                    import json
                    plan = json.loads(response)
                    state.plan = plan
                    state.current_step = 0
                except json.JSONDecodeError:
                    # Fallback to simple plan
                    state.plan = [{"action": "analyze_page", "element": "page", "value": "", "expected_result": "Page analyzed"}]
            
            self.logger.info("Plan created", steps=len(state.plan))
            
        except Exception as e:
            self.logger.error("Planning failed", error=str(e))
            state.error_log.append(f"Planning error: {str(e)}")
        
        return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execution node in the LangGraph workflow"""
        try:
            if state.current_step < len(state.plan):
                step = state.plan[state.current_step]
                
                # Validate action with policy agent
                is_valid, validation_message = await self.policy_agent.validate_action(
                    step["action"], state.current_url, {}
                )
                
                if not is_valid:
                    state.error_log.append(f"Policy violation: {validation_message}")
                    return state
                
                # Execute the action
                result = await self._execute_browser_action(step)
                
                # Update state
                if result.get("success"):
                    state.current_step += 1
                    if "data" in result:
                        state.extracted_data.update(result["data"])
                else:
                    state.error_log.append(result.get("error", "Unknown execution error"))
            
            self.logger.info("Execution completed", step=state.current_step)
            
        except Exception as e:
            self.logger.error("Execution failed", error=str(e))
            state.error_log.append(f"Execution error: {str(e)}")
        
        return state
    
    async def _reflect_node(self, state: AgentState) -> AgentState:
        """Reflection node for quality assurance and learning"""
        try:
            # Analyze current state and progress
            reflection_prompt = f"""
            Analyze the current browser automation progress:
            
            Task: {state.task_description}
            Completed steps: {state.current_step}/{len(state.plan)}
            Recent errors: {state.error_log[-3:] if state.error_log else 'None'}
            Extracted data: {len(state.extracted_data)} items
            
            Determine:
            1. Is the task complete?
            2. Are there any issues that need addressing?
            3. Should we continue, retry, or finish?
            
            Respond with: COMPLETE, CONTINUE, or RETRY
            """
            
            if self.ollama_client and await self.ollama_client.check_health():
                response = await self.ollama_client.generate(
                    model=self.ollama_model,
                    prompt=reflection_prompt
                )
                
                state.memory["reflection"] = response.strip()
            
            self.logger.info("Reflection completed")
            
        except Exception as e:
            self.logger.error("Reflection failed", error=str(e))
            state.error_log.append(f"Reflection error: {str(e)}")
        
        return state
    
    async def _memory_store_node(self, state: AgentState) -> AgentState:
        """Store experiences in long-term memory"""
        try:
            # Store the complete task experience
            context = f"Task: {state.task_description}, Steps: {len(state.plan)}, Errors: {len(state.error_log)}"
            result = f"Completed: {state.current_step}/{len(state.plan)}, Data extracted: {len(state.extracted_data)} items"
            
            await self.memory_manager.store_experience(
                action="complete_task",
                context=context,
                result=result,
                url=state.current_url
            )
            
            self.logger.info("Experience stored in memory")
            
        except Exception as e:
            self.logger.error("Memory storage failed", error=str(e))
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Conditional logic for workflow continuation"""
        reflection = state.memory.get("reflection", "").upper()
        
        if "COMPLETE" in reflection or state.current_step >= len(state.plan):
            return "memory"
        elif "RETRY" in reflection and len(state.error_log) < 3:
            return "continue"
        elif state.current_step < len(state.plan) and len(state.error_log) < 3:
            return "continue"
        else:
            return "memory"  # End with memory storage
    
    async def _execute_browser_action(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific browser action"""
        try:
            action = step["action"]
            element = step.get("element", "")
            value = step.get("value", "")
            
            if not self.page:
                return {"success": False, "error": "No active page"}
            
            # Take screenshot for vision analysis
            screenshot_path = f"./screenshots/step_{int(time.time())}.png"
            await self.page.screenshot(path=screenshot_path)
            
            # Analyze screenshot with vision agent
            vision_analysis = await self.vision_agent.analyze_screenshot(
                screenshot_path, f"{action} {element}"
            )
            
            # Execute action based on type
            if action == "click":
                result = await self._click_element(element, vision_analysis)
            elif action == "type":
                result = await self._type_text(element, value, vision_analysis)
            elif action == "navigate":
                result = await self._navigate_to_url(value)
            elif action == "extract":
                result = await self._extract_data(element, vision_analysis)
            elif action == "wait":
                result = await self._wait_for_element(element)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            return result
            
        except Exception as e:
            self.logger.error("Browser action failed", action=step.get("action"), error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _click_element(self, element_description: str, vision_analysis: Dict) -> Dict[str, Any]:
        """Click on an element using vision guidance"""
        try:
            # Find best matching element from vision analysis
            buttons = vision_analysis.get("buttons", [])
            text_areas = vision_analysis.get("text_areas", [])
            
            # Simple matching logic - can be enhanced with better AI
            target_element = None
            for button in buttons:
                if button.get("confidence", 0) > 0.5:
                    target_element = button
                    break
            
            if not target_element and text_areas:
                for text_area in text_areas:
                    if element_description.lower() in text_area.get("text", "").lower():
                        target_element = text_area
                        break
            
            if target_element:
                bbox = target_element["bbox"]
                center_x = bbox["x"] + bbox["width"] // 2
                center_y = bbox["y"] + bbox["height"] // 2
                
                await self.page.mouse.click(center_x, center_y)
                
                return {"success": True, "action": "click", "coordinates": (center_x, center_y)}
            else:
                return {"success": False, "error": f"Element not found: {element_description}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _type_text(self, element_description: str, text: str, vision_analysis: Dict) -> Dict[str, Any]:
        """Type text into an element"""
        try:
            # Try to find input fields
            try:
                await self.page.fill(f"input:has-text('{element_description}')", text)
                return {"success": True, "action": "type", "text": text}
            except:
                # Fallback to vision-based typing
                forms = vision_analysis.get("forms", [])
                if forms:
                    form = forms[0]
                    bbox = form["bbox"]
                    center_x = bbox["x"] + bbox["width"] // 2
                    center_y = bbox["y"] + bbox["height"] // 2
                    
                    await self.page.mouse.click(center_x, center_y)
                    await self.page.keyboard.type(text)
                    
                    return {"success": True, "action": "type", "text": text}
                else:
                    return {"success": False, "error": f"Input field not found: {element_description}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL"""
        try:
            await self.page.goto(url, wait_until="load")
            return {"success": True, "action": "navigate", "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _extract_data(self, element_description: str, vision_analysis: Dict) -> Dict[str, Any]:
        """Extract data from the page"""
        try:
            extracted_data = {}
            
            # Extract text from vision analysis
            text_areas = vision_analysis.get("text_areas", [])
            for text_area in text_areas:
                if text_area.get("confidence", 0) > 0.5:
                    text = text_area.get("text", "").strip()
                    if text:
                        extracted_data[f"text_{len(extracted_data)}"] = text
            
            # Extract page title and URL
            extracted_data["title"] = await self.page.title()
            extracted_data["url"] = self.page.url
            
            return {"success": True, "action": "extract", "data": extracted_data}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _wait_for_element(self, element_description: str) -> Dict[str, Any]:
        """Wait for an element to appear"""
        try:
            # Simple wait implementation
            await self.page.wait_for_timeout(2000)  # Wait 2 seconds
            return {"success": True, "action": "wait"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def initialize_browser(self, headless: bool = True):
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=headless)
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            self.page = await self.context.new_page()
            
            # Create screenshots directory
            import os
            os.makedirs("./screenshots", exist_ok=True)
            
            self.logger.info("Browser initialized")
            
        except Exception as e:
            self.logger.error("Browser initialization failed", error=str(e))
            raise
    
    async def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            
            self.logger.info("Browser closed")
            
        except Exception as e:
            self.logger.error("Browser cleanup failed", error=str(e))
    
    @tracer.start_as_current_span("execute_task")
    async def execute_task(self, task_description: str, starting_url: str = "") -> Dict[str, Any]:
        """
        Main entry point for executing browser automation tasks
        
        Args:
            task_description: Natural language description of the task
            starting_url: Optional starting URL
            
        Returns:
            Dictionary with task results, extracted data, and metadata
        """
        try:
            # Initialize state
            initial_state = AgentState(
                task_description=task_description,
                current_url=starting_url
            )
            
            # Initialize browser if not already done
            if not self.page:
                await self.initialize_browser()
            
            # Navigate to starting URL if provided
            if starting_url:
                await self.page.goto(starting_url, wait_until="load")
                initial_state.current_url = self.page.url
            
            # Execute workflow
            if self.workflow:
                config = {"configurable": {"thread_id": str(uuid.uuid4())}}
                result_state = await self.workflow.ainvoke(initial_state, config)
            else:
                # Fallback to simple execution
                result_state = await self._simple_task_execution(initial_state)
            
            # Prepare results
            results = {
                "success": True,
                "task_description": task_description,
                "steps_completed": result_state.current_step,
                "total_steps": len(result_state.plan),
                "extracted_data": result_state.extracted_data,
                "screenshots": result_state.screenshots,
                "errors": result_state.error_log,
                "final_url": self.page.url if self.page else "",
                "execution_time": time.time()
            }
            
            self.logger.info("Task completed", 
                           task=task_description,
                           steps=result_state.current_step,
                           errors=len(result_state.error_log))
            
            return results
            
        except Exception as e:
            self.logger.error("Task execution failed", task=task_description, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "task_description": task_description
            }
    
    async def _simple_task_execution(self, state: AgentState) -> AgentState:
        """Fallback simple task execution without LangGraph"""
        try:
            # Simple plan: navigate and extract
            state.plan = [
                {"action": "analyze_page", "element": "page", "value": "", "expected_result": "Page analyzed"},
                {"action": "extract", "element": "content", "value": "", "expected_result": "Data extracted"}
            ]
            
            # Execute each step
            for i, step in enumerate(state.plan):
                state.current_step = i
                result = await self._execute_browser_action(step)
                
                if result.get("success"):
                    if "data" in result:
                        state.extracted_data.update(result["data"])
                else:
                    state.error_log.append(result.get("error", "Unknown error"))
                    break
            
            state.current_step = len(state.plan)
            
        except Exception as e:
            state.error_log.append(f"Simple execution error: {str(e)}")
        
        return state
    
    def _init_cloudflare_clients(self):
        """Initialize Cloudflare clients for edge computing and AI"""
        try:
            # Initialize hybrid inference client (Ollama + Cloudflare Workers AI)
            self.hybrid_client = HybridInferenceClient(self.cloudflare_config)
            
            # Initialize Durable Objects client for state management
            if hasattr(self.cloudflare_config, 'account_id') and hasattr(self.cloudflare_config, 'api_token'):
                # Use environment variable for namespace or default
                namespace = os.getenv('CLOUDFLARE_KV_NAMESPACE', 'orbit-agents-state')
                self.durable_objects_client = DurableObjectsClient(
                    self.cloudflare_config.account_id,
                    self.cloudflare_config.api_token,
                    namespace
                )
            
            self.logger.info("Cloudflare clients initialized", 
                           hybrid_inference=bool(self.hybrid_client),
                           durable_objects=bool(self.durable_objects_client))
            
        except Exception as e:
            self.logger.error("Cloudflare initialization failed", error=str(e))
            self.hybrid_client = None
            self.durable_objects_client = None

class RealEstateScrapingAgent:
    """Specialized agent for robust real estate website scraping"""
    
    def __init__(self, page: Page, logger):
        self.page = page
        self.logger = logger
        
        # Real estate field mapping with multiple selector strategies
        self.field_selectors = {
            "price": [
                "[data-testid*='price']",
                ".price", ".listing-price", ".home-price", 
                "[class*='price']", "[id*='price']",
                "span:contains('$')", "div:contains('$')"
            ],
            "address": [
                "[data-testid*='address']",
                ".address", ".listing-address", ".property-address",
                "[class*='address']", "[id*='address']",
                "h1", "h2:contains(',')"
            ],
            "bedrooms": [
                "[data-testid*='bed']",
                ".beds", ".bedrooms", "[class*='bed']",
                "span:contains('bed')", "div:contains('bed')"
            ],
            "bathrooms": [
                "[data-testid*='bath']",
                ".baths", ".bathrooms", "[class*='bath']",
                "span:contains('bath')", "div:contains('bath')"
            ],
            "sqft": [
                "[data-testid*='sqft']", "[data-testid*='square']",
                ".sqft", ".square-feet", "[class*='sqft']",
                "span:contains('sqft')", "span:contains('sq ft')"
            ],
            "description": [
                "[data-testid*='description']",
                ".description", ".property-description", 
                ".listing-description", "[class*='description']"
            ],
            "features": [
                ".features", ".amenities", ".property-features",
                "[class*='feature']", "[class*='amenity']"
            ],
            "images": [
                ".gallery img", ".photos img", ".listing-photos img",
                ".property-images img", "[class*='photo'] img"
            ]
        }
        
        # Common real estate patterns
        self.price_patterns = [
            r'\$[\d,]+',
            r'\$\s*\d+(?:,\d{3})*',
            r'Price:\s*\$[\d,]+',
            r'Listed at \$[\d,]+'
        ]
        
        self.bed_bath_patterns = [
            r'(\d+)\s*bed',
            r'(\d+)\s*bedroom',
            r'(\d+)\s*Bath',
            r'(\d+)\s*bathroom'
        ]
        
        self.sqft_patterns = [
            r'([\d,]+)\s*sqft',
            r'([\d,]+)\s*sq\.?\s*ft',
            r'([\d,]+)\s*square\s*feet'
        ]
    
    async def extract_listing_data(self, url: str) -> Dict[str, Any]:
        """Extract comprehensive listing data with multiple fallback strategies"""
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for content to load
            await self.page.wait_for_timeout(2000)
            
            # Try to close any modals/popups
            await self._close_modals()
            
            # Extract using multiple strategies
            structured_data = await self._extract_structured_data()
            selector_data = await self._extract_with_selectors()
            text_pattern_data = await self._extract_with_patterns()
            vision_data = await self._extract_with_vision()
            
            # Merge and validate results
            merged_data = self._merge_extraction_results([
                structured_data,
                selector_data,
                text_pattern_data,
                vision_data
            ])
            
            # Add metadata
            merged_data.update({
                "url": url,
                "domain": urlparse(url).netloc,
                "extracted_at": datetime.now().isoformat(),
                "extraction_confidence": self._calculate_confidence(merged_data)
            })
            
            self.logger.info("Listing data extracted", 
                           url=url, 
                           fields_found=len([k for k, v in merged_data.items() if v]))
            
            return merged_data
            
        except Exception as e:
            self.logger.error("Failed to extract listing data", url=url, error=str(e))
            return {"error": str(e), "url": url}
    
    async def _close_modals(self):
        """Close common modal dialogs and popups"""
        modal_selectors = [
            "[data-testid*='modal'] button[aria-label*='close']",
            ".modal .close", ".popup .close", ".overlay .close",
            "button:contains('Close')", "button:contains('×')",
            "[aria-label='Close']", "[aria-label='close']"
        ]
        
        for selector in modal_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await self.page.wait_for_timeout(500)
            except:
                continue
    
    async def _extract_structured_data(self) -> Dict[str, Any]:
        """Extract data from JSON-LD structured data"""
        data = {}
        try:
            # Look for JSON-LD structured data
            json_ld_elements = await self.page.query_selector_all('script[type="application/ld+json"]')
            
            for element in json_ld_elements:
                try:
                    content = await element.inner_text()
                    json_data = json.loads(content)
                    
                    # Extract real estate specific fields
                    if isinstance(json_data, dict):
                        if json_data.get("@type") in ["RealEstateListing", "Product", "Place"]:
                            offers = json_data.get("offers", {})
                            if isinstance(offers, dict):
                                price = offers.get("price") or offers.get("priceSpecification", {}).get("price")
                                if price:
                                    data["price"] = str(price)
                            
                            address = json_data.get("address", {})
                            if isinstance(address, dict):
                                full_address = ", ".join(filter(None, [
                                    address.get("streetAddress"),
                                    address.get("addressLocality"),
                                    address.get("addressRegion"),
                                    address.get("postalCode")
                                ]))
                                if full_address:
                                    data["address"] = full_address
                            
                            # Extract property details
                            if "numberOfRooms" in json_data:
                                data["bedrooms"] = str(json_data["numberOfRooms"])
                            
                            if "floorSize" in json_data:
                                data["sqft"] = str(json_data["floorSize"])
                                
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            self.logger.debug("Structured data extraction failed", error=str(e))
        
        return data
    
    async def _extract_with_selectors(self) -> Dict[str, Any]:
        """Extract data using CSS selectors with fallback strategies"""
        data = {}
        
        for field, selectors in self.field_selectors.items():
            for selector in selectors:
                try:
                    if field == "images":
                        # Handle images specially
                        elements = await self.page.query_selector_all(selector)
                        urls = []
                        for element in elements[:10]:  # Limit to 10 images
                            src = await element.get_attribute("src")
                            if src:
                                urls.append(urljoin(self.page.url, src))
                        if urls:
                            data[field] = urls
                            break
                    else:
                        # Handle text content
                        element = await self.page.query_selector(selector)
                        if element:
                            text = await element.inner_text()
                            if text and text.strip():
                                data[field] = text.strip()
                                break
                except:
                    continue
        
        return data
    
    async def _extract_with_patterns(self) -> Dict[str, Any]:
        """Extract data using regex patterns on page text"""
        data = {}
        
        try:
            page_text = await self.page.inner_text("body")
            
            # Extract price
            for pattern in self.price_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    data["price"] = matches[0]
                    break
            
            # Extract bedrooms/bathrooms
            bed_matches = []
            bath_matches = []
            
            for pattern in self.bed_bath_patterns:
                if "bed" in pattern.lower():
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    bed_matches.extend(matches)
                else:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    bath_matches.extend(matches)
            
            if bed_matches:
                data["bedrooms"] = bed_matches[0]
            if bath_matches:
                data["bathrooms"] = bath_matches[0]
            
            # Extract square footage
            for pattern in self.sqft_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    data["sqft"] = matches[0].replace(",", "")
                    break
                    
        except Exception as e:
            self.logger.debug("Pattern extraction failed", error=str(e))
        
        return data
    
    async def _extract_with_vision(self) -> Dict[str, Any]:
        """Extract data using vision analysis (placeholder for future enhancement)"""
        # This would use computer vision to identify and extract data from screenshots
        # For now, return empty dict
        return {}
    
    def _merge_extraction_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge results from multiple extraction strategies with confidence scoring"""
        merged = {}
        field_sources = defaultdict(list)
        
        # Collect all values for each field
        for i, result in enumerate(results):
            for field, value in result.items():
                if value and field != "error":
                    field_sources[field].append((value, i))
        
        # Choose best value for each field
        for field, values in field_sources.items():
            if not values:
                continue
                
            # Prefer structured data (index 0), then selectors (index 1)
            if any(source_idx == 0 for _, source_idx in values):
                merged[field] = next(value for value, source_idx in values if source_idx == 0)
            elif any(source_idx == 1 for _, source_idx in values):
                merged[field] = next(value for value, source_idx in values if source_idx == 1)
            else:
                # Use first available value
                merged[field] = values[0][0]
        
        return merged
    
    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate extraction confidence based on fields found"""
        critical_fields = ["price", "address", "bedrooms", "bathrooms"]
        found_critical = sum(1 for field in critical_fields if data.get(field))
        
        total_fields = len([k for k, v in data.items() if v and k not in ["url", "domain", "extracted_at"]])
        
        confidence = (found_critical / len(critical_fields)) * 0.7 + (min(total_fields, 8) / 8) * 0.3
        return round(confidence, 2)

# Factory function for creating the agent
def create_enhanced_browser_agent(**kwargs) -> EnhancedBrowserAgent:
    """Factory function to create an enhanced browser agent"""
    return EnhancedBrowserAgent(**kwargs)


# Example usage and testing
async def test_enhanced_agent():
    """Test function for the enhanced browser agent"""
    agent = create_enhanced_browser_agent(
        use_ollama=True,
        ollama_model="mixtral:8x22b"
    )
    
    try:
        # Test task
        result = await agent.execute_task(
            task_description="Navigate to example.com and extract the main content",
            starting_url="https://example.com"
        )
        
        print("Task Result:", json.dumps(result, indent=2))
        
    finally:
        await agent.close_browser()


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_enhanced_agent())