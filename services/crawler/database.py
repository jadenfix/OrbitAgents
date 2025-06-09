"""
Database Models and Connection Management
SQLAlchemy models for PostgreSQL with comprehensive listings schema.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, AsyncGenerator
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, Boolean, JSON,
    Index, UniqueConstraint, BigInteger
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import mapped_column, Mapped

from config import settings
import structlog

logger = structlog.get_logger(__name__)

# SQLAlchemy declarative base
Base = declarative_base()


class Listing(Base):
    """
    Listings table model for storing normalized MLS data.
    Optimized for search queries and geographic operations.
    """
    __tablename__ = "listings"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    # MLS identifier (unique within the system)
    mls_id: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        index=True,
        doc="Original MLS listing ID"
    )
    
    # Core property attributes
    beds: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True, 
        index=True,
        doc="Number of bedrooms"
    )
    baths: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True, 
        index=True,
        doc="Number of bathrooms"
    )
    price: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        nullable=True, 
        index=True,
        doc="Price in cents"
    )
    
    # Geographic coordinates (for PostGIS compatibility)
    latitude: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True, 
        index=True,
        doc="Latitude coordinate"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True, 
        index=True,
        doc="Longitude coordinate"
    )
    
    # Property details
    property_type: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True, 
        index=True,
        doc="Property type (single_family, condo, etc.)"
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True, 
        index=True,
        doc="Listing status (active, pending, sold, etc.)"
    )
    square_feet: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True, 
        index=True,
        doc="Square footage"
    )
    lot_size_acres: Mapped[Optional[float]] = mapped_column(
        Float, 
        nullable=True,
        doc="Lot size in acres"
    )
    year_built: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True, 
        index=True,
        doc="Year built"
    )
    
    # Address components
    street_address: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Street address"
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100), 
        nullable=True, 
        index=True,
        doc="City"
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(2), 
        nullable=True, 
        index=True,
        doc="State abbreviation"
    )
    zip_code: Mapped[Optional[str]] = mapped_column(
        String(10), 
        nullable=True, 
        index=True,
        doc="ZIP code"
    )
    
    # Rich content
    description: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Property description"
    )
    listing_agent: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        doc="Listing agent name"
    )
    photo_urls: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True,
        doc="Photo URLs as JSON array"
    )
    
    # Timestamps
    mls_last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        doc="Last updated timestamp from MLS"
    )
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc),
        index=True,
        doc="When this record was crawled"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        doc="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(), 
        onupdate=func.now(),
        doc="Record last update timestamp"
    )
    
    # Data lineage
    raw_data_s3_key: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        doc="S3 key for raw MLS data"
    )
    data_source: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        default="mls_api",
        doc="Source of the data"
    )
    data_version: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="1.0",
        doc="Data schema version"
    )
    
    # Soft delete support
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True, 
        index=True,
        doc="Whether this listing is active"
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        doc="Soft delete timestamp"
    )

    # Table constraints and indexes
    __table_args__ = (
        # Unique constraint for MLS ID (prevent duplicates)
        UniqueConstraint("mls_id", name="uq_listings_mls_id"),
        
        # Composite indexes for common query patterns
        Index("idx_listings_price_beds_baths", "price", "beds", "baths"),
        Index("idx_listings_location", "latitude", "longitude"),
        Index("idx_listings_city_state", "city", "state"),
        Index("idx_listings_property_type_status", "property_type", "status"),
        Index("idx_listings_crawled_at_active", "crawled_at", "is_active"),
        
        # Search optimization indexes
        Index("idx_listings_search_basic", "beds", "baths", "price", "property_type", "is_active"),
        Index("idx_listings_geographic", "latitude", "longitude", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Listing(mls_id='{self.mls_id}', beds={self.beds}, baths={self.baths}, price={self.price})>"

    @property
    def price_dollars(self) -> Optional[float]:
        """Convert price from cents to dollars."""
        return self.price / 100.0 if self.price is not None else None

    @property
    def has_coordinates(self) -> bool:
        """Check if listing has valid geographic coordinates."""
        return (
            self.latitude is not None 
            and self.longitude is not None 
            and -90 <= self.latitude <= 90 
            and -180 <= self.longitude <= 180
        )


class CrawlJob(Base):
    """
    Crawl job tracking table for monitoring and debugging.
    """
    __tablename__ = "crawl_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    
    job_id: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        unique=True, 
        index=True,
        doc="Unique job identifier"
    )
    
    status: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="running",
        doc="Job status (running, completed, failed)"
    )
    
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc),
        doc="Job start time"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        doc="Job completion time"
    )
    
    # Statistics
    total_fetched: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Total listings fetched from MLS"
    )
    total_processed: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Total listings processed"
    )
    total_saved: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Total listings saved to database"
    )
    total_indexed: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Total listings indexed in OpenSearch"
    )
    total_errors: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Total errors encountered"
    )
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Error message if job failed"
    )
    error_details: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True,
        doc="Detailed error information"
    )
    
    # Configuration
    config_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True,
        doc="Configuration used for this job"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now()
    )

    __table_args__ = (
        Index("idx_crawl_jobs_status_started", "status", "started_at"),
        Index("idx_crawl_jobs_completed", "completed_at"),
    )

    def __repr__(self) -> str:
        return f"<CrawlJob(job_id='{self.job_id}', status='{self.status}')>"


# Database engine and session management
class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self.engine = None
        self.session_maker = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connection and create tables."""
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.postgres_url.replace("postgresql://", "postgresql+asyncpg://"),
                pool_size=settings.postgres_pool_size,
                max_overflow=settings.postgres_max_overflow,
                pool_pre_ping=True,
                echo=settings.debug,
                future=True
            )
            
            # Create session maker
            self.session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Database initialized successfully", 
                       postgres_url=settings.postgres_url.split("@")[-1])  # Hide credentials
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with proper cleanup."""
        if not self._initialized:
            await self.initialize()
        
        async with self.session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session_maker() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency function for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async with db_manager.get_session() as session:
        yield session 