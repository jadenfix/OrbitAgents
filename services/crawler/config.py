"""
Crawler Service Configuration
Comprehensive settings for MLS data crawling, storage, and indexing.
"""

import os
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Crawler service configuration with comprehensive validation."""
    
    # Service Configuration
    service_name: str = Field(default="crawler", description="Service name")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # MLS API Configuration
    mls_api_url: str = Field(
        default="https://api.example-mls.com/listings",
        description="MLS API endpoint URL"
    )
    mls_api_key: Optional[str] = Field(default=None, description="MLS API key")
    mls_timeout: int = Field(default=30, description="MLS API timeout in seconds")
    mls_retry_attempts: int = Field(default=3, description="Maximum retry attempts for MLS API")
    mls_retry_delay: int = Field(default=5, description="Delay between retries in seconds")
    
    # Scheduling Configuration
    crawler_cron: str = Field(
        default="0 */4 * * *",  # Every 4 hours
        description="Cron expression for crawler schedule"
    )
    enable_scheduler: bool = Field(default=True, description="Enable automatic scheduling")
    
    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="orbit_listings", description="PostgreSQL database name")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="", description="PostgreSQL password")
    postgres_pool_size: int = Field(default=10, description="PostgreSQL connection pool size")
    postgres_max_overflow: int = Field(default=20, description="PostgreSQL max pool overflow")
    
    @property
    def postgres_url(self) -> str:
        """Construct PostgreSQL connection URL."""
        if self.postgres_password:
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        return f"postgresql://{self.postgres_user}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # S3 Configuration
    s3_bucket: str = Field(default="orbit-mls-data", description="S3 bucket for raw data storage")
    s3_region: str = Field(default="us-west-2", description="S3 region")
    s3_access_key_id: Optional[str] = Field(default=None, description="S3 access key ID")
    s3_secret_access_key: Optional[str] = Field(default=None, description="S3 secret access key")
    s3_endpoint_url: Optional[str] = Field(default=None, description="S3 endpoint URL (for localstack)")
    s3_raw_data_prefix: str = Field(default="raw", description="S3 prefix for raw data")
    
    # OpenSearch Configuration
    opensearch_host: str = Field(default="localhost", description="OpenSearch host")
    opensearch_port: int = Field(default=9200, description="OpenSearch port")
    opensearch_scheme: str = Field(default="http", description="OpenSearch scheme")
    opensearch_username: Optional[str] = Field(default=None, description="OpenSearch username")
    opensearch_password: Optional[str] = Field(default=None, description="OpenSearch password")
    opensearch_index: str = Field(default="listings_dev", description="OpenSearch index name")
    opensearch_timeout: int = Field(default=30, description="OpenSearch timeout in seconds")
    opensearch_max_retries: int = Field(default=3, description="OpenSearch max retries")
    
    @property
    def opensearch_url(self) -> str:
        """Construct OpenSearch connection URL."""
        auth = ""
        if self.opensearch_username and self.opensearch_password:
            auth = f"{self.opensearch_username}:{self.opensearch_password}@"
        return f"{self.opensearch_scheme}://{auth}{self.opensearch_host}:{self.opensearch_port}"
    
    # Redis Configuration (for Celery)
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Data Processing Configuration
    batch_size: int = Field(default=100, description="Batch size for processing listings")
    max_listings_per_run: int = Field(default=10000, description="Maximum listings to process per run")
    enable_data_validation: bool = Field(default=True, description="Enable data validation")
    
    # Error Handling Configuration
    max_consecutive_failures: int = Field(default=5, description="Max consecutive failures before alerting")
    failure_cooldown_minutes: int = Field(default=30, description="Cooldown period after failures")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=8001, description="Metrics server port")
    health_check_timeout: int = Field(default=10, description="Health check timeout in seconds")
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v.lower()
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "CRAWLER_",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()

# Environment-specific overrides
if settings.environment == "production":
    settings.debug = False
    settings.log_level = "WARNING"
elif settings.environment == "development":
    settings.debug = True
    settings.log_level = "DEBUG" 