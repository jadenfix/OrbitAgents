"""
Configuration management for Auth Service with enhanced validation
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables with validation."""
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/orbitagents",
        description="Database connection URL"
    )
    
    # JWT Configuration
    JWT_SECRET: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT signing secret",
        min_length=32
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_MINUTES: int = Field(
        default=15, 
        description="JWT token expiration in minutes",
        ge=1,
        le=1440  # Maximum 24 hours
    )
    
    # Service Configuration
    SERVICE_NAME: str = Field(default="auth", description="Service name")
    SERVICE_VERSION: str = Field(default="1.0.0", description="Service version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,https://orbitagents.dev",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # API Keys (for other services to use)
    ANTHROPIC_API_KEY: Optional[str] = Field(
        default=None,
        description="Anthropic API key for AI services"
    )
    ANTHROPIC_MODEL: str = Field(
        default="claude-3-haiku-20240307",
        description="Anthropic model to use"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    LOGIN_RATE_LIMIT: int = Field(
        default=10,
        description="Login attempts per time window",
        ge=1,
        le=100
    )
    REGISTER_RATE_LIMIT: int = Field(
        default=5,
        description="Registration attempts per time window",
        ge=1,
        le=50
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=300,
        description="Rate limit time window in seconds",
        ge=60,
        le=3600
    )
    
    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret strength."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long")
        
        # In production, ensure it's not the default
        if v == "your-secret-key-change-in-production":
            import warnings
            warnings.warn(
                "Using default JWT_SECRET in production is dangerous! "
                "Please set a secure JWT_SECRET environment variable.",
                UserWarning
            )
        
        return v
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("DATABASE_URL is required")
        
        # Basic format validation
        if not (v.startswith(('postgresql://', 'sqlite:///', 'mysql://'))):
            raise ValueError(
                "DATABASE_URL must start with postgresql://, sqlite:///, or mysql://"
            )
        
        return v
    
    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_allowed_origins(cls, v: str) -> str:
        """Validate CORS origins."""
        if not v:
            raise ValueError("ALLOWED_ORIGINS is required")
        
        # Split by comma and validate each origin
        origins = [origin.strip() for origin in v.split(',')]
        
        for origin in origins:
            if not origin:
                continue
                
            # Allow localhost and standard patterns
            if origin == "*":
                import warnings
                warnings.warn(
                    "Using wildcard (*) for ALLOWED_ORIGINS in production is dangerous!",
                    UserWarning
                )
                continue
            
            if not (
                origin.startswith(('http://', 'https://')) or
                origin.startswith('localhost') or
                origin.startswith('127.0.0.1')
            ):
                raise ValueError(f"Invalid CORS origin format: {origin}")
        
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

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Create settings instance
settings = Settings() 