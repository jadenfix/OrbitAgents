"""
Configuration management for Query Service with comprehensive validation
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field, ConfigDict


class Settings(BaseSettings):
    """Application settings with comprehensive validation and edge case handling."""
    
    # Service Configuration
    SERVICE_NAME: str = Field(default="query", description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8001, description="Server port", ge=1, le=65535)
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis password"
    )
    CACHE_TTL: int = Field(
        default=86400,  # 24 hours
        description="Cache TTL in seconds",
        ge=300,  # Minimum 5 minutes
        le=604800  # Maximum 7 days
    )
    
    # OpenSearch Configuration
    OPENSEARCH_URL: str = Field(
        default="https://localhost:9200",
        description="OpenSearch cluster URL"
    )
    OPENSEARCH_USERNAME: str = Field(
        default="admin",
        description="OpenSearch username"
    )
    OPENSEARCH_PASSWORD: str = Field(
        default="admin",
        description="OpenSearch password"
    )
    OPENSEARCH_INDEX: str = Field(
        default="listings_dev",
        description="OpenSearch index name",
        min_length=1,
        max_length=255
    )
    OPENSEARCH_VERIFY_CERTS: bool = Field(
        default=False,
        description="Verify OpenSearch SSL certificates"
    )
    
    # NLU Configuration
    SPACY_MODEL: str = Field(
        default="en_core_web_sm",
        description="spaCy model name"
    )
    MAX_QUERY_LENGTH: int = Field(
        default=500,
        description="Maximum query length",
        ge=10,
        le=2000
    )
    
    # Search Configuration
    DEFAULT_SEARCH_LIMIT: int = Field(
        default=10,
        description="Default search result limit",
        ge=1,
        le=100
    )
    MAX_SEARCH_LIMIT: int = Field(
        default=100,
        description="Maximum search result limit",
        ge=1,
        le=1000
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    PARSE_RATE_LIMIT: int = Field(
        default=100,
        description="Parse requests per minute",
        ge=1,
        le=1000
    )
    SEARCH_RATE_LIMIT: int = Field(
        default=50,
        description="Search requests per minute",
        ge=1,
        le=500
    )
    
    # Geographic Configuration
    DEFAULT_SEARCH_RADIUS: str = Field(
        default="50km",
        description="Default search radius for geo queries"
    )
    MAX_SEARCH_RADIUS: str = Field(
        default="500km",
        description="Maximum search radius"
    )
    
    # API Keys (for external services)
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key for advanced NLU"
    )
    
    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v:
            raise ValueError("REDIS_URL is required")
        
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError("REDIS_URL must start with redis:// or rediss://")
        
        return v
    
    @field_validator("OPENSEARCH_URL")
    @classmethod
    def validate_opensearch_url(cls, v: str) -> str:
        """Validate OpenSearch URL format."""
        if not v:
            raise ValueError("OPENSEARCH_URL is required")
        
        if not v.startswith(('http://', 'https://')):
            raise ValueError("OPENSEARCH_URL must start with http:// or https://")
        
        return v
    
    @field_validator("OPENSEARCH_INDEX")
    @classmethod
    def validate_opensearch_index(cls, v: str) -> str:
        """Validate OpenSearch index name."""
        if not v:
            raise ValueError("OPENSEARCH_INDEX is required")
        
        # OpenSearch index naming rules
        if v.lower() != v:
            raise ValueError("OpenSearch index name must be lowercase")
        
        invalid_chars = ['\\', '/', '*', '?', '"', '<', '>', '|', ' ', ',', '#']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"OpenSearch index name contains invalid characters: {invalid_chars}")
        
        if v.startswith(('-', '_', '+')):
            raise ValueError("OpenSearch index name cannot start with -, _, or +")
        
        return v
    
    @field_validator("DEFAULT_SEARCH_RADIUS", "MAX_SEARCH_RADIUS")
    @classmethod
    def validate_search_radius(cls, v: str) -> str:
        """Validate search radius format."""
        import re
        
        if not re.match(r'^\d+(\.\d+)?(km|mi|m)$', v):
            raise ValueError("Search radius must be in format: number + unit (km, mi, m)")
        
        return v
    
    @field_validator("ANTHROPIC_API_KEY")
    @classmethod
    def validate_anthropic_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate Anthropic API key format."""
        if v and v not in ['test-key'] and not v.startswith('sk-ant-'):
            raise ValueError("ANTHROPIC_API_KEY must start with 'sk-ant-'")
        return v
    
    @field_validator("DEBUG")
    @classmethod
    def validate_debug_mode(cls, v: bool) -> bool:
        """Validate debug mode setting."""
        if v:
            import warnings
            warnings.warn(
                "DEBUG mode is enabled. This should not be used in production!",
                UserWarning
            )
        return v

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
        str_strip_whitespace=True
    )


# Create settings instance
settings = Settings() 