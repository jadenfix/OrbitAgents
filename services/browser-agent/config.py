"""
Browser Agent Service Configuration
Free-tier settings for browser automation.
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Browser Agent service configuration with free-tier optimizations."""
    
    # Service Configuration
    service_name: str = Field(default="browser-agent", description="Service name")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Browser Configuration
    default_browser: str = Field(default="chromium", description="Default browser type")
    headless: bool = Field(default=True, description="Run browsers in headless mode")
    max_concurrent_browsers: int = Field(default=3, description="Max concurrent browser instances")
    browser_timeout: int = Field(default=30000, description="Browser timeout in milliseconds")
    
    # Redis Configuration (Free)
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # File Storage Configuration
    screenshots_dir: str = Field(default="screenshots", description="Screenshots directory")
    downloads_dir: str = Field(default="downloads", description="Downloads directory")
    max_file_size: int = Field(default=10485760, description="Max file size in bytes (10MB)")
    
    # Rate Limiting
    max_requests_per_minute: int = Field(default=60, description="Max requests per minute")
    max_tasks_per_user: int = Field(default=5, description="Max concurrent tasks per user")
    
    # WebSocket Configuration
    websocket_timeout: int = Field(default=300, description="WebSocket timeout in seconds")
    max_websocket_connections: int = Field(default=100, description="Max WebSocket connections")
    
    # Security Configuration
    allowed_domains: list[str] = Field(
        default=["*"], 
        description="Allowed domains for automation (use * for all)"
    )
    block_private_ips: bool = Field(default=True, description="Block private IP addresses")
    
    # Performance Configuration
    page_load_timeout: int = Field(default=30000, description="Page load timeout in ms")
    element_timeout: int = Field(default=5000, description="Element timeout in ms")
    navigation_timeout: int = Field(default=30000, description="Navigation timeout in ms")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=8001, description="Metrics server port")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
