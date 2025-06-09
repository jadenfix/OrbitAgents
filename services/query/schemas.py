"""
Pydantic schemas for Query Service with comprehensive validation and edge case handling
"""

import re
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class PropertyType(str, Enum):
    """Property type enumeration."""
    APARTMENT = "apartment"
    HOUSE = "house"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    STUDIO = "studio"
    OTHER = "other"


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class SortBy(str, Enum):
    """Sort by field enumeration."""
    PRICE = "price"
    BEDS = "beds"
    BATHS = "baths"
    DISTANCE = "distance"
    RELEVANCE = "relevance"
    DATE_ADDED = "date_added"


class ParseRequest(BaseModel):
    """Schema for query parsing requests."""
    
    query: str = Field(
        ...,
        description="Natural language query to parse",
        min_length=1,
        max_length=500,
        examples=[
            "2 bedroom apartment in San Francisco under $3000",
            "house with 3+ bedrooms in downtown Seattle",
            "condo near Golden Gate Park with parking"
        ]
    )
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Comprehensive query validation."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        
        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v.strip())
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script injection
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers
            r'(union|select|insert|update|delete|drop)\s+',  # SQL injection
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Query contains potentially malicious content')
        
        # Check for excessive repetitive characters
        if re.search(r'(.)\1{10,}', v):
            raise ValueError('Query contains excessive repetitive characters')
        
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "query": "2 bedroom apartment in San Francisco under $3000"
            }
        }
    )


class ParsedQuery(BaseModel):
    """Schema for parsed query results."""
    
    beds: Optional[int] = Field(
        None,
        description="Number of bedrooms",
        ge=0,
        le=20
    )
    beds_min: Optional[int] = Field(
        None,
        description="Minimum number of bedrooms",
        ge=0,
        le=20
    )
    beds_max: Optional[int] = Field(
        None,
        description="Maximum number of bedrooms",
        ge=0,
        le=20
    )
    
    baths: Optional[float] = Field(
        None,
        description="Number of bathrooms",
        ge=0,
        le=20
    )
    baths_min: Optional[float] = Field(
        None,
        description="Minimum number of bathrooms",
        ge=0,
        le=20
    )
    baths_max: Optional[float] = Field(
        None,
        description="Maximum number of bathrooms",
        ge=0,
        le=20
    )
    
    city: Optional[str] = Field(
        None,
        description="City name",
        min_length=1,
        max_length=100
    )
    
    neighborhoods: List[str] = Field(
        default_factory=list,
        description="Neighborhood names",
        max_length=10
    )
    
    max_price: Optional[float] = Field(
        None,
        description="Maximum price",
        ge=0,
        le=100000000  # $100M max
    )
    min_price: Optional[float] = Field(
        None,
        description="Minimum price",
        ge=0,
        le=100000000
    )
    
    property_type: Optional[PropertyType] = Field(
        None,
        description="Property type"
    )
    
    keywords: List[str] = Field(
        default_factory=list,
        description="Additional keywords extracted",
        max_length=20
    )
    
    has_parking: Optional[bool] = Field(
        None,
        description="Parking requirement"
    )
    has_pets: Optional[bool] = Field(
        None,
        description="Pet-friendly requirement"
    )
    has_furnished: Optional[bool] = Field(
        None,
        description="Furnished requirement"
    )
    
    confidence: float = Field(
        default=0.0,
        description="Parse confidence score",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('city')
    @classmethod
    def validate_city(cls, v: Optional[str]) -> Optional[str]:
        """Validate city name."""
        if v is None:
            return v
        
        # Basic sanitization
        v = re.sub(r'[^\w\s\-\.]', '', v)
        v = v.strip().title()
        
        if len(v) < 2:
            raise ValueError('City name too short')
        
        return v
    
    @field_validator('neighborhoods')
    @classmethod
    def validate_neighborhoods(cls, v: List[str]) -> List[str]:
        """Validate neighborhood names."""
        validated = []
        for neighborhood in v:
            if neighborhood and len(neighborhood.strip()) >= 2:
                clean = re.sub(r'[^\w\s\-\.]', '', neighborhood).strip().title()
                if clean:
                    validated.append(clean)
        return validated[:10]  # Limit to 10 neighborhoods
    
    @field_validator('keywords')
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate keywords."""
        validated = []
        for keyword in v:
            if keyword and len(keyword.strip()) >= 2:
                clean = re.sub(r'[^\w\s\-]', '', keyword).strip().lower()
                if clean and clean not in validated:
                    validated.append(clean)
        return validated[:20]  # Limit to 20 keywords

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "beds": 2,
                "baths": 1.5,
                "city": "San Francisco",
                "max_price": 3000.0,
                "property_type": "apartment",
                "confidence": 0.85
            }
        }
    )


class GeoPoint(BaseModel):
    """Geographic point schema."""
    
    lat: float = Field(
        ...,
        description="Latitude",
        ge=-90,
        le=90
    )
    lon: float = Field(
        ...,
        description="Longitude", 
        ge=-180,
        le=180
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "lat": 37.7749,
                "lon": -122.4194
            }
        }
    )


class SearchFilters(BaseModel):
    """Schema for search filters."""
    
    beds: Optional[int] = Field(None, ge=0, le=20)
    beds_min: Optional[int] = Field(None, ge=0, le=20)
    beds_max: Optional[int] = Field(None, ge=0, le=20)
    
    baths: Optional[float] = Field(None, ge=0, le=20)
    baths_min: Optional[float] = Field(None, ge=0, le=20)
    baths_max: Optional[float] = Field(None, ge=0, le=20)
    
    price_min: Optional[float] = Field(None, ge=0, le=100000000)
    price_max: Optional[float] = Field(None, ge=0, le=100000000)
    
    property_type: Optional[PropertyType] = None
    
    location: Optional[GeoPoint] = None
    radius: Optional[str] = Field(None, pattern=r'^\d+(\.\d+)?(km|mi|m)$')
    
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    neighborhoods: List[str] = Field(default_factory=list, max_length=10)
    
    has_parking: Optional[bool] = None
    has_pets: Optional[bool] = None
    has_furnished: Optional[bool] = None
    
    keywords: List[str] = Field(default_factory=list, max_length=20)


class SearchRequest(BaseModel):
    """Schema for search requests."""
    
    filters: SearchFilters = Field(default_factory=SearchFilters)
    
    limit: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=100
    )
    
    offset: int = Field(
        default=0,
        description="Number of results to skip",
        ge=0,
        le=10000
    )
    
    sort_by: SortBy = Field(
        default=SortBy.RELEVANCE,
        description="Sort field"
    )
    
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort order"
    )
    
    include_score: bool = Field(
        default=False,
        description="Include relevance scores"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filters": {
                    "beds_min": 2,
                    "price_max": 3000.0,
                    "city": "San Francisco",
                    "property_type": "apartment"
                },
                "limit": 10,
                "sort_by": "price",
                "sort_order": "asc"
            }
        }
    )


class PropertyListing(BaseModel):
    """Schema for property listing results."""
    
    id: str = Field(..., description="Unique listing ID")
    price: float = Field(..., description="Property price", ge=0)
    beds: int = Field(..., description="Number of bedrooms", ge=0)
    baths: float = Field(..., description="Number of bathrooms", ge=0)
    
    location: GeoPoint = Field(..., description="Property location")
    address: str = Field(..., description="Property address")
    city: str = Field(..., description="City")
    neighborhood: Optional[str] = Field(None, description="Neighborhood")
    
    property_type: PropertyType = Field(..., description="Property type")
    
    title: str = Field(..., description="Listing title")
    description: Optional[str] = Field(None, description="Property description")
    
    amenities: List[str] = Field(default_factory=list, description="Property amenities")
    
    images: List[str] = Field(default_factory=list, description="Image URLs")
    
    date_added: datetime = Field(..., description="Date listing was added")
    date_updated: Optional[datetime] = Field(None, description="Date listing was updated")
    
    score: Optional[float] = Field(None, description="Relevance score", ge=0, le=1)
    
    distance: Optional[float] = Field(None, description="Distance from search location in km")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "listing_123",
                "price": 2800.0,
                "beds": 2,
                "baths": 1.5,
                "location": {"lat": 37.7749, "lon": -122.4194},
                "address": "123 Main St",
                "city": "San Francisco",
                "property_type": "apartment",
                "title": "Beautiful 2BR Apartment in SOMA"
            }
        }
    )


class SearchResponse(BaseModel):
    """Schema for search responses."""
    
    results: List[PropertyListing] = Field(
        default_factory=list,
        description="Search results"
    )
    
    total: int = Field(
        default=0,
        description="Total number of matching results",
        ge=0
    )
    
    limit: int = Field(..., description="Results limit used")
    offset: int = Field(..., description="Results offset used")
    
    query_time_ms: float = Field(
        ...,
        description="Query execution time in milliseconds",
        ge=0
    )
    
    filters_applied: SearchFilters = Field(
        ...,
        description="Filters that were applied"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [],
                "total": 45,
                "limit": 10,
                "offset": 0,
                "query_time_ms": 125.5,
                "filters_applied": {}
            }
        }
    )


class HealthCheck(BaseModel):
    """Schema for health check responses."""
    
    status: str = Field(..., pattern="^(healthy|unhealthy)$")
    timestamp: datetime = Field(..., description="Health check timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Dependency status"
    )
    
    uptime_seconds: float = Field(
        ...,
        description="Service uptime in seconds",
        ge=0
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "service": "query",
                "version": "1.0.0",
                "dependencies": {
                    "redis": "connected",
                    "opensearch": "connected"
                },
                "uptime_seconds": 3600.5
            }
        }
    )


class SearchPipelineRequest(BaseModel):
    """Schema for search pipeline requests."""
    
    q: str = Field(
        ...,
        description="Natural language query to parse and search",
        min_length=1,
        max_length=500,
        examples=[
            "3 bedroom house under $600k in Denver",
            "2 bed apartment near downtown with parking",
            "condo with 2+ baths under $400000"
        ]
    )
    
    limit: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=100
    )
    
    include_parse_details: bool = Field(
        default=True,
        description="Include parsed query details in response"
    )
    
    @field_validator('q')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query using same rules as ParseRequest."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        
        # Remove excessive whitespace
        v = re.sub(r'\s+', ' ', v.strip())
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',
            r'javascript:',
            r'on\w+\s*=',
            r'(union|select|insert|update|delete|drop)\s+',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Query contains potentially malicious content')
        
        if re.search(r'(.)\1{10,}', v):
            raise ValueError('Query contains excessive repetitive characters')
        
        return v

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "q": "3 bedroom house under $600k in Denver",
                "limit": 10,
                "include_parse_details": True
            }
        }
    )


class SearchPipelineResponse(BaseModel):
    """Schema for search pipeline responses."""
    
    query: str = Field(..., description="Original query")
    
    parse: Optional[ParsedQuery] = Field(
        None,
        description="Parsed query details (if include_parse_details=True)"
    )
    
    listings: List[PropertyListing] = Field(
        default_factory=list,
        description="Search results"
    )
    
    total: int = Field(
        default=0,
        description="Total number of matching results",
        ge=0
    )
    
    limit: int = Field(..., description="Results limit used")
    
    parse_time_ms: float = Field(
        ...,
        description="Parse execution time in milliseconds",
        ge=0
    )
    
    search_time_ms: float = Field(
        ...,
        description="Search execution time in milliseconds", 
        ge=0
    )
    
    total_time_ms: float = Field(
        ...,
        description="Total pipeline execution time in milliseconds",
        ge=0
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "3 bedroom house under $600k in Denver",
                "parse": {
                    "beds": 3,
                    "max_price": 600000,
                    "city": "Denver",
                    "property_type": "house",
                    "confidence": 0.95
                },
                "listings": [
                    {
                        "id": "listing-123",
                        "price": 575000,
                        "beds": 3,
                        "baths": 2.5,
                        "location": {"lat": 39.7392, "lon": -104.9903},
                        "address": "123 Main St",
                        "city": "Denver",
                        "property_type": "house",
                        "title": "Beautiful 3BR House in Denver",
                        "date_added": "2024-01-01T12:00:00Z"
                    }
                ],
                "total": 45,
                "limit": 10,
                "parse_time_ms": 15.2,
                "search_time_ms": 32.8,
                "total_time_ms": 48.0
            }
        }
    )


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "validation_error",
                "message": "Invalid query format",
                "details": {
                    "field": "query",
                    "issue": "Query too short"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
    ) 