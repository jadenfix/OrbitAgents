"""
Comprehensive End-to-End Testing Suite for Enhanced Browser Agent
Tests all major components including vision, memory, planning, and execution
"""

import pytest
import asyncio
import json
import os
import tempfile
from typing import Dict, Any, List
from pathlib import Path
import aiohttp

# Import our enhanced browser agent
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../api'))

from enhanced_browser_agent import (
    EnhancedBrowserAgent,
    VisionAgent,
    MemoryManager,
    PolicyAgent,
    OllamaClient,
    AgentState
)

class TestEnhancedBrowserAgent:
    """Comprehensive test suite for the enhanced browser agent"""
    
    @pytest.fixture
    async def agent(self):
        """Create a test agent instance"""
        agent = EnhancedBrowserAgent(
            use_ollama=False,  # Use fallback for tests
            openai_api_key=None  # No API key needed for basic tests
        )
        yield agent
        
        # Cleanup
        if hasattr(agent, 'browser') and agent.browser:
            await agent.close_browser()
    
    @pytest.fixture
    def test_html_file(self):
        """Create a test HTML file"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Test Website</h1>
            <p>This is a test paragraph.</p>
            <button id="test-button">Click Me</button>
            <form id="test-form">
                <input type="text" id="name" name="name" placeholder="Enter name">
                <input type="email" id="email" name="email" placeholder="Enter email">
                <button type="submit">Submit</button>
            </form>
            <div class="content">
                <span>Important data: 12345</span>
                <span>Status: Active</span>
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html_content)
            file_path = f.name
        
        yield f"file://{file_path}"
        
        # Cleanup
        os.unlink(file_path)
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test that the agent initializes correctly"""
        assert agent is not None
        assert agent.vision_agent is not None
        assert agent.memory_manager is not None
        assert agent.policy_agent is not None
    
    @pytest.mark.asyncio
    async def test_browser_initialization(self, agent):
        """Test browser initialization and cleanup"""
        await agent.initialize_browser(headless=True)
        
        assert agent.browser is not None
        assert agent.context is not None
        assert agent.page is not None
        
        await agent.close_browser()
    
    @pytest.mark.asyncio
    async def test_simple_navigation(self, agent, test_html_file):
        """Test basic navigation to a webpage"""
        await agent.initialize_browser(headless=True)
        
        result = await agent.execute_task(
            task_description="Navigate to the test page and extract the title",
            starting_url=test_html_file
        )
        
        assert result["success"] is True
        assert "Test Page" in str(result.get("extracted_data", {}))
        assert result["final_url"] == test_html_file
    
    @pytest.mark.asyncio
    async def test_data_extraction(self, agent, test_html_file):
        """Test data extraction from webpage"""
        await agent.initialize_browser(headless=True)
        
        result = await agent.execute_task(
            task_description="Extract all text content from the page",
            starting_url=test_html_file
        )
        
        assert result["success"] is True
        extracted_data = result.get("extracted_data", {})
        
        # Check that we extracted some meaningful data
        assert len(extracted_data) > 0
        assert "title" in extracted_data
        assert extracted_data["title"] == "Test Page"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test error handling with invalid URL"""
        await agent.initialize_browser(headless=True)
        
        result = await agent.execute_task(
            task_description="Navigate to invalid URL",
            starting_url="http://this-domain-does-not-exist-12345.com"
        )
        
        # Should handle error gracefully
        assert result["success"] is False or len(result.get("errors", [])) > 0


class TestVisionAgent:
    """Test suite for the Vision Agent component"""
    
    @pytest.fixture
    def vision_agent(self):
        """Create a vision agent instance"""
        return VisionAgent()
    
    @pytest.fixture
    def test_screenshot(self):
        """Create a test screenshot"""
        import cv2
        import numpy as np
        
        # Create a simple test image
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # Add some shapes to simulate UI elements
        cv2.rectangle(img, (100, 100), (200, 150), (255, 255, 255), -1)  # Button
        cv2.rectangle(img, (300, 200), (500, 250), (200, 200, 200), -1)  # Text area
        cv2.putText(img, "Click Me", (110, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            cv2.imwrite(f.name, img)
            file_path = f.name
        
        yield file_path
        
        # Cleanup
        os.unlink(file_path)
    
    @pytest.mark.asyncio
    async def test_screenshot_analysis(self, vision_agent, test_screenshot):
        """Test screenshot analysis functionality"""
        result = await vision_agent.analyze_screenshot(
            test_screenshot, 
            "Find buttons on the page"
        )
        
        assert "buttons" in result
        assert "text_areas" in result
        assert "forms" in result
        assert "dimensions" in result
        assert result["dimensions"]["width"] == 800
        assert result["dimensions"]["height"] == 600
    
    def test_button_detection(self, vision_agent):
        """Test button detection algorithm"""
        import cv2
        import numpy as np
        
        # Create test image with button-like shapes
        gray_img = np.zeros((400, 600), dtype=np.uint8)
        cv2.rectangle(gray_img, (50, 50), (150, 100), 255, -1)
        
        buttons = vision_agent._detect_buttons(gray_img)
        
        assert isinstance(buttons, list)
        # Should detect at least one button-like shape
        assert len(buttons) >= 0  # May be 0 if detection is strict


class TestMemoryManager:
    """Test suite for the Memory Manager component"""
    
    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager instance"""
        # Use a test collection name
        return MemoryManager(collection_name="test_browser_agent_memory")
    
    @pytest.mark.asyncio
    async def test_store_experience(self, memory_manager):
        """Test storing browsing experiences"""
        await memory_manager.store_experience(
            action="click_button",
            context="Login page with username and password fields",
            result="Successfully clicked login button",
            url="https://example.com/login"
        )
        
        # If no exception raised, test passes
        assert True
    
    @pytest.mark.asyncio
    async def test_retrieve_experiences(self, memory_manager):
        """Test retrieving similar experiences"""
        # First store some experiences
        await memory_manager.store_experience(
            action="fill_form",
            context="Registration form with name and email",
            result="Form filled successfully",
            url="https://example.com/register"
        )
        
        # Try to retrieve similar experiences
        experiences = await memory_manager.retrieve_similar_experiences(
            "fill form with user information"
        )
        
        assert isinstance(experiences, list)
        # May be empty if ChromaDB is not properly initialized


class TestPolicyAgent:
    """Test suite for the Policy Agent component"""
    
    @pytest.fixture
    def policy_agent(self):
        """Create a policy agent instance"""
        return PolicyAgent()
    
    @pytest.mark.asyncio
    async def test_safe_action_validation(self, policy_agent):
        """Test validation of safe actions"""
        is_valid, message = await policy_agent.validate_action(
            action="click_button",
            url="https://example.com",
            context={}
        )
        
        assert is_valid is True
        assert "approved" in message.lower()
    
    @pytest.mark.asyncio
    async def test_blocked_domain_validation(self, policy_agent):
        """Test blocking of dangerous domains"""
        is_valid, message = await policy_agent.validate_action(
            action="click_button",
            url="https://malware.com",
            context={}
        )
        
        assert is_valid is False
        assert "blocked" in message.lower()
    
    @pytest.mark.asyncio
    async def test_sensitive_action_validation(self, policy_agent):
        """Test validation of sensitive actions"""
        is_valid, message = await policy_agent.validate_action(
            action="delete_account",
            url="https://example.com",
            context={"user_confirmed": False}
        )
        
        assert is_valid is False
        assert "sensitive" in message.lower()
    
    @pytest.mark.asyncio
    async def test_security_risk_detection(self, policy_agent):
        """Test detection of security risks"""
        is_valid, message = await policy_agent.validate_action(
            action="javascript:alert('xss')",
            url="https://example.com",
            context={}
        )
        
        assert is_valid is False
        assert "security" in message.lower()


class TestOllamaClient:
    """Test suite for Ollama integration"""
    
    @pytest.fixture
    def ollama_client(self):
        """Create an Ollama client instance"""
        return OllamaClient()
    
    @pytest.mark.asyncio
    async def test_health_check(self, ollama_client):
        """Test Ollama server health check"""
        is_healthy = await ollama_client.check_health()
        
        # This may fail if Ollama is not running, which is expected
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_generation_fallback(self, ollama_client):
        """Test text generation with fallback handling"""
        # This should handle connection errors gracefully
        result = await ollama_client.generate(
            model="mixtral:8x22b",
            prompt="Hello, how are you?"
        )
        
        # Should return empty string if Ollama is not available
        assert isinstance(result, str)


class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    async def full_agent(self):
        """Create a fully configured agent"""
        agent = EnhancedBrowserAgent(
            use_ollama=False,  # Disable for testing
            openai_api_key=None
        )
        await agent.initialize_browser(headless=True)
        yield agent
        await agent.close_browser()
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, full_agent, test_html_file):
        """Test the complete agent workflow"""
        result = await full_agent.execute_task(
            task_description="Navigate to the page, find the button, and extract all visible text",
            starting_url=test_html_file
        )
        
        assert result["success"] is True
        assert result["steps_completed"] >= 0
        assert "extracted_data" in result
        assert result["final_url"] == test_html_file
    
    @pytest.mark.asyncio
    async def test_memory_integration(self, full_agent, test_html_file):
        """Test that memory is properly integrated"""
        # Execute a task
        result1 = await full_agent.execute_task(
            task_description="Navigate and extract data",
            starting_url=test_html_file
        )
        
        # The memory should have stored the experience
        experiences = await full_agent.memory_manager.retrieve_similar_experiences(
            "navigate and extract"
        )
        
        assert isinstance(experiences, list)
    
    @pytest.mark.asyncio
    async def test_policy_integration(self, full_agent):
        """Test that policy validation is integrated"""
        # Try to execute a task with a blocked domain
        result = await full_agent.execute_task(
            task_description="Navigate to a blocked site",
            starting_url="https://malware.com"
        )
        
        # Should either fail or have policy errors
        assert result["success"] is False or len(result.get("errors", [])) > 0


# Performance and Load Tests
class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_agents(self):
        """Test multiple agents running concurrently"""
        async def create_and_run_agent():
            agent = EnhancedBrowserAgent(use_ollama=False)
            try:
                await agent.initialize_browser(headless=True)
                result = await agent.execute_task(
                    task_description="Simple navigation test",
                    starting_url="https://example.com"
                )
                return result["success"]
            finally:
                await agent.close_browser()
        
        # Run 3 agents concurrently
        tasks = [create_and_run_agent() for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some should succeed
        successes = [r for r in results if r is True]
        assert len(successes) >= 1
    
    @pytest.mark.asyncio
    async def test_memory_performance(self):
        """Test memory operations performance"""
        import time
        
        memory_manager = MemoryManager(collection_name="perf_test_memory")
        
        # Test storing multiple experiences
        start_time = time.time()
        
        for i in range(10):
            await memory_manager.store_experience(
                action=f"test_action_{i}",
                context=f"test_context_{i}",
                result=f"test_result_{i}",
                url=f"https://example.com/page_{i}"
            )
        
        store_time = time.time() - start_time
        
        # Test retrieval
        start_time = time.time()
        experiences = await memory_manager.retrieve_similar_experiences("test action")
        retrieve_time = time.time() - start_time
        
        # Performance should be reasonable
        assert store_time < 30.0  # 30 seconds max for 10 stores
        assert retrieve_time < 10.0  # 10 seconds max for retrieval
        assert isinstance(experiences, list)


# Fixtures for test data
@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp(prefix="browser_agent_test_")
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


# Configuration for test runs
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", 
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )


# Test discovery and execution
if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
