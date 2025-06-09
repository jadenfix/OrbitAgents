"""
Crawler Service Data Schemas
Pydantic models for MLS listings, database entities, and API responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum


class PropertyType(str, Enum):
    """Property type enumeration."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"
    OTHER = "other"


class ListingStatus(str, Enum):
    """Listing status enumeration."""
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    OFF_MARKET = "off_market"
    WITHDRAWN = "withdrawn"


class GeographicCoordinates(BaseModel):
    """Geographic coordinates model."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    lon: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )


class MLSRawListing(BaseModel):
    """Raw MLS listing data model - matches API response."""
    id: str = Field(..., min_length=1, description="Unique MLS listing ID")
    beds: Optional[int] = Field(None, ge=0, le=50, description="Number of bedrooms")
    baths: Optional[float] = Field(None, ge=0, le=50, description="Number of bathrooms")
    price: Optional[int] = Field(None, ge=0, description="Listing price in cents")
    lat: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    lon: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Complete raw MLS data")
    
    # Additional common MLS fields
    property_type: Optional[str] = Field(None, description="Property type")
    status: Optional[str] = Field(None, description="Listing status")
    square_feet: Optional[int] = Field(None, ge=0, description="Square footage")
    lot_size: Optional[float] = Field(None, ge=0, description="Lot size in acres")
    year_built: Optional[int] = Field(None, ge=1800, le=2030, description="Year built")
    address: Optional[str] = Field(None, description="Property address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, max_length=2, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    description: Optional[str] = Field(None, description="Property description")
    listing_agent: Optional[str] = Field(None, description="Listing agent name")
    photos: Optional[List[str]] = Field(default_factory=list, description="Photo URLs")
    last_updated: Optional[datetime] = Field(None, description="Last updated timestamp")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow"  # Allow extra fields from MLS API
    )
    
    @validator("price")
    def validate_price(cls, v):
        """Validate price is reasonable."""
        if v is not None and (v < 0 or v > 100_000_000_00):  # $100M max
            raise ValueError("Price must be between $0 and $100,000,000")
        return v
    
    @validator("zip_code")
    def validate_zip_code(cls, v):
        """Validate ZIP code format."""
        if v is not None:
            # Basic ZIP code validation (5 or 9 digits)
            import re
            if not re.match(r'^\d{5}(-\d{4})?$', v.strip()):
                raise ValueError("Invalid ZIP code format")
        return v
    
    @property
    def coordinates(self) -> Optional[GeographicCoordinates]:
        """Get coordinates if both lat and lon are available."""
        if self.lat is not None and self.lon is not None:
            return GeographicCoordinates(lat=self.lat, lon=self.lon)
        return None


class NormalizedListing(BaseModel):
    """Normalized listing data for database storage."""
    mls_id: str = Field(..., description="Original MLS ID")
    beds: Optional[int] = Field(None, description="Number of bedrooms")
    baths: Optional[float] = Field(None, description="Number of bathrooms")
    price: Optional[int] = Field(None, description="Price in cents")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    
    # Normalized additional fields
    property_type: Optional[PropertyType] = Field(None, description="Normalized property type")
    status: Optional[ListingStatus] = Field(None, description="Normalized listing status")
    square_feet: Optional[int] = Field(None, description="Square footage")
    lot_size_acres: Optional[float] = Field(None, description="Lot size in acres")
    year_built: Optional[int] = Field(None, description="Year built")
    
    # Address components
    street_address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State abbreviation")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    
    # Metadata
    description: Optional[str] = Field(None, description="Property description")
    listing_agent: Optional[str] = Field(None, description="Listing agent")
    photo_urls: List[str] = Field(default_factory=list, description="Photo URLs")
    
    # Timestamps
    mls_last_updated: Optional[datetime] = Field(None, description="MLS last updated")
    crawled_at: datetime = Field(default_factory=datetime.utcnow, description="Crawl timestamp")
    
    # Raw data reference
    raw_data_s3_key: Optional[str] = Field(None, description="S3 key for raw data")
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True
    )
    
    @classmethod
    def from_mls_listing(cls, mls_listing: MLSRawListing, s3_key: Optional[str] = None) -> "NormalizedListing":
        """Create normalized listing from raw MLS data."""
        return cls(
            mls_id=mls_listing.id,
            beds=mls_listing.beds,
            baths=mls_listing.baths,
            price=mls_listing.price,
            latitude=mls_listing.lat,
            longitude=mls_listing.lon,
            property_type=cls._normalize_property_type(mls_listing.property_type),
            status=cls._normalize_status(mls_listing.status),
            square_feet=mls_listing.square_feet,
            lot_size_acres=mls_listing.lot_size,
            year_built=mls_listing.year_built,
            street_address=mls_listing.address,
            city=mls_listing.city,
            state=mls_listing.state,
            zip_code=mls_listing.zip_code,
            description=mls_listing.description,
            listing_agent=mls_listing.listing_agent,
            photo_urls=mls_listing.photos or [],
            mls_last_updated=mls_listing.last_updated,
            raw_data_s3_key=s3_key
        )
    
    @staticmethod
    def _normalize_property_type(raw_type: Optional[str]) -> Optional[PropertyType]:
        """Normalize property type from raw MLS data."""
        if not raw_type:
            return None
        
        raw_type_lower = raw_type.lower().strip()
        type_mapping = {
            "single family": PropertyType.SINGLE_FAMILY,
            "single-family": PropertyType.SINGLE_FAMILY,
            "sfr": PropertyType.SINGLE_FAMILY,
            "house": PropertyType.SINGLE_FAMILY,
            "condo": PropertyType.CONDO,
            "condominium": PropertyType.CONDO,
            "townhouse": PropertyType.TOWNHOUSE,
            "townhome": PropertyType.TOWNHOUSE,
            "multi-family": PropertyType.MULTI_FAMILY,
            "multifamily": PropertyType.MULTI_FAMILY,
            "duplex": PropertyType.MULTI_FAMILY,
            "land": PropertyType.LAND,
            "lot": PropertyType.LAND,
            "commercial": PropertyType.COMMERCIAL,
        }
        
        return type_mapping.get(raw_type_lower, PropertyType.OTHER)
    
    @staticmethod
    def _normalize_status(raw_status: Optional[str]) -> Optional[ListingStatus]:
        """Normalize listing status from raw MLS data."""
        if not raw_status:
            return None
        
        raw_status_lower = raw_status.lower().strip()
        status_mapping = {
            "active": ListingStatus.ACTIVE,
            "for sale": ListingStatus.ACTIVE,
            "pending": ListingStatus.PENDING,
            "under contract": ListingStatus.PENDING,
            "sold": ListingStatus.SOLD,
            "closed": ListingStatus.SOLD,
            "off market": ListingStatus.OFF_MARKET,
            "withdrawn": ListingStatus.WITHDRAWN,
            "cancelled": ListingStatus.WITHDRAWN,
        }
        
        return status_mapping.get(raw_status_lower, ListingStatus.ACTIVE)


class OpenSearchListing(BaseModel):
    """OpenSearch document model for listings."""
    mls_id: str
    beds: Optional[int] = None
    baths: Optional[float] = None
    price: Optional[int] = None
    location: Optional[Dict[str, float]] = None  # {"lat": float, "lon": float}
    property_type: Optional[str] = None
    status: Optional[str] = None
    square_feet: Optional[int] = None
    year_built: Optional[int] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    description: Optional[str] = None
    crawled_at: datetime
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )
    
    @classmethod
    def from_normalized_listing(cls, listing: NormalizedListing) -> "OpenSearchListing":
        """Create OpenSearch document from normalized listing."""
        location = None
        if listing.latitude is not None and listing.longitude is not None:
            location = {"lat": listing.latitude, "lon": listing.longitude}
        
        return cls(
            mls_id=listing.mls_id,
            beds=listing.beds,
            baths=listing.baths,
            price=listing.price,
            location=location,
            property_type=listing.property_type.value if listing.property_type else None,
            status=listing.status.value if listing.status else None,
            square_feet=listing.square_feet,
            year_built=listing.year_built,
            city=listing.city,
            state=listing.state,
            zip_code=listing.zip_code,
            description=listing.description,
            crawled_at=listing.crawled_at
        )


class CrawlJobStatus(BaseModel):
    """Crawl job status and statistics."""
    job_id: str
    status: str  # "running", "completed", "failed"
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Statistics
    total_fetched: int = 0
    total_processed: int = 0
    total_saved: int = 0
    total_indexed: int = 0
    total_errors: int = 0
    
    # Error details
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class MLSApiResponse(BaseModel):
    """MLS API response wrapper."""
    listings: List[MLSRawListing]
    total_count: Optional[int] = None
    page: Optional[int] = None
    per_page: Optional[int] = None
    has_more: bool = False
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    
    # Service health details
    database_healthy: bool = True
    s3_healthy: bool = True
    opensearch_healthy: bool = True
    mls_api_healthy: bool = True
    
    # Last successful crawl
    last_crawl_at: Optional[datetime] = None
    last_crawl_status: Optional[str] = None
    
    model_config = ConfigDict(
        str_strip_whitespace=True
    ) 