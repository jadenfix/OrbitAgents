"""
Query Service - FastAPI application for NLU parsing and property search
with comprehensive error handling, rate limiting, and monitoring.
"""

import os
import time
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
import asyncio

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, status, Query as QueryParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import structlog

from config import settings
from schemas import (
    ParseRequest, ParsedQuery, SearchRequest, SearchResponse, 
    HealthCheck, ErrorResponse, SearchFilters, PropertyListing
)
from nlu_parser import NLUParser
from cache_manager import cache_manager
from opensearch_client import opensearch_client

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = structlog.get_logger(__name__)

# Initialize NLU parser
nlu_parser = NLUParser(model_name=settings.SPACY_MODEL)

# Rate limiting storage (in-memory for simplicity)
rate_limit_storage: Dict[str, Dict[str, Any]] = {}

# Service metrics
service_metrics = {
    'start_time': time.time(),
    'parse_requests': 0,
    'search_requests': 0,
    'error_count': 0,
    'cache_hits': 0,
    'cache_misses': 0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Query Service", version=settings.SERVICE_VERSION)
    
    # Initialize services
    await cache_manager.initialize()
    await opensearch_client.initialize()
    
    logger.info("Query Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Query Service")
    await cache_manager.close()
    logger.info("Query Service shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Query Service",
    description="Advanced NLU parsing and property search service",
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Dependency functions
async def get_client_ip(request: Request) -> str:
    """Get client IP address for rate limiting."""
    # Check for forwarded headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def check_rate_limit(endpoint: str, limit: int) -> bool:
    """Simple in-memory rate limiting."""
    if not settings.RATE_LIMIT_ENABLED:
        return True
    
    def rate_limit_dependency(request: Request):
        client_ip = asyncio.create_task(get_client_ip(request))
        current_time = time.time()
        window = 60  # 1 minute window
        
        key = f"{client_ip}:{endpoint}"
        
        if key not in rate_limit_storage:
            rate_limit_storage[key] = {'requests': [], 'blocked_until': 0}
        
        entry = rate_limit_storage[key]
        
        # Check if still blocked
        if current_time < entry['blocked_until']:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Clean old requests
        entry['requests'] = [
            req_time for req_time in entry['requests'] 
            if current_time - req_time < window
        ]
        
        # Check rate limit
        if len(entry['requests']) >= limit:
            entry['blocked_until'] = current_time + window
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per minute."
            )
        
        # Add current request
        entry['requests'].append(current_time)
        return True
    
    return rate_limit_dependency


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    service_metrics['error_count'] += 1
    
    logger.warning(
        "Validation error",
        path=request.url.path,
        errors=exc.errors(),
        body=await request.body() if hasattr(request, 'body') else None
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="validation_error",
            message="Invalid request data",
            details={"errors": exc.errors()}
        ).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors."""
    service_metrics['error_count'] += 1
    
    logger.warning(
        "Value error",
        path=request.url.path,
        error=str(exc)
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="value_error",
            message=str(exc)
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    service_metrics['error_count'] += 1
    
    logger.error(
        "Unexpected error",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred"
        ).model_dump()
    )


# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "service": "Query Service",
        "version": settings.SERVICE_VERSION,
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Comprehensive health check endpoint."""
    # Check service dependencies
    dependencies = {}
    
    # Check Redis
    if await cache_manager.health_check():
        dependencies["redis"] = "connected"
    else:
        dependencies["redis"] = "disconnected"
    
    # Check OpenSearch
    if await opensearch_client.health_check():
        dependencies["opensearch"] = "connected"
    else:
        dependencies["opensearch"] = "disconnected"
    
    # Determine overall status
    status_value = "healthy" if all(
        status == "connected" for status in dependencies.values()
    ) else "unhealthy"
    
    uptime = time.time() - service_metrics['start_time']
    
    return HealthCheck(
        status=status_value,
        timestamp=datetime.now(timezone.utc),
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        dependencies=dependencies,
        uptime_seconds=uptime
    )


@app.get("/parse", response_model=ParsedQuery)
async def parse_query(
    q: str = QueryParam(..., description="Natural language query to parse"),
    _rate_limit: bool = Depends(check_rate_limit("parse", settings.PARSE_RATE_LIMIT))
):
    """
    Parse a natural language query into structured data.
    
    This endpoint uses advanced NLU techniques including spaCy and regex patterns
    to extract property search criteria from natural language queries.
    
    Examples:
    - "2 bedroom apartment in San Francisco under $3000"
    - "house with 3+ bedrooms in downtown Seattle"
    - "condo near Golden Gate Park with parking"
    """
    service_metrics['parse_requests'] += 1
    start_time = time.time()
    
    try:
        # Validate query length
        if len(q) > settings.MAX_QUERY_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query too long. Maximum length is {settings.MAX_QUERY_LENGTH} characters."
            )
        
        # Check cache first
        cached_result = await cache_manager.get_parsed_query(q)
        if cached_result:
            service_metrics['cache_hits'] += 1
            logger.info(
                "Cache hit for parse query",
                query=q[:50] + "..." if len(q) > 50 else q,
                response_time_ms=(time.time() - start_time) * 1000
            )
            return ParsedQuery(**cached_result['parsed_data'])
        
        service_metrics['cache_misses'] += 1
        
        # Parse query
        parsed_result = nlu_parser.parse_query(q)
        
        # Cache result
        await cache_manager.set_parsed_query(q, parsed_result.model_dump())
        
        response_time = (time.time() - start_time) * 1000
        
        logger.info(
            "Parsed query successfully",
            query=q[:50] + "..." if len(q) > 50 else q,
            confidence=parsed_result.confidence,
            response_time_ms=response_time
        )
        
        return parsed_result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Error parsing query",
            query=q,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse query"
        )


@app.post("/search", response_model=SearchResponse)
async def search_properties(
    request: SearchRequest,
    _rate_limit: bool = Depends(check_rate_limit("search", settings.SEARCH_RATE_LIMIT))
):
    """
    Search for properties using structured filters.
    
    This endpoint accepts parsed query data and searches the OpenSearch index
    for matching properties with comprehensive filtering and sorting options.
    """
    service_metrics['search_requests'] += 1
    start_time = time.time()
    
    try:
        # Validate search limits
        if request.limit > settings.MAX_SEARCH_LIMIT:
            request.limit = settings.MAX_SEARCH_LIMIT
        
        # Generate cache key for search
        search_key = hashlib.sha256(
            request.model_dump_json().encode()
        ).hexdigest()[:16]
        
        # Check cache
        cached_results = await cache_manager.get_search_results(search_key)
        if cached_results:
            service_metrics['cache_hits'] += 1
            logger.info(
                "Cache hit for search",
                filters=request.filters.model_dump(),
                response_time_ms=(time.time() - start_time) * 1000
            )
            return SearchResponse(**cached_results)
        
        service_metrics['cache_misses'] += 1
        
        # Perform search
        results, total_count, query_time = await opensearch_client.search_properties(
            filters=request.filters,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by.value,
            sort_order=request.sort_order.value
        )
        
        # Convert results to PropertyListing objects
        property_listings = []
        for result in results:
            try:
                # Ensure required fields are present
                if all(field in result for field in ['id', 'price', 'beds', 'baths', 'location', 'address', 'city', 'property_type', 'title', 'date_added']):
                    listing = PropertyListing(**result)
                    if not request.include_score:
                        listing.score = None
                    property_listings.append(listing)
            except Exception as e:
                logger.warning(f"Error converting search result to PropertyListing: {e}")
                continue
        
        response_time = (time.time() - start_time) * 1000
        
        # Build response
        search_response = SearchResponse(
            results=property_listings,
            total=total_count,
            limit=request.limit,
            offset=request.offset,
            query_time_ms=response_time,
            filters_applied=request.filters
        )
        
        # Cache results
        await cache_manager.set_search_results(search_key, search_response.model_dump())
        
        logger.info(
            "Search completed successfully",
            results_count=len(property_listings),
            total_matches=total_count,
            query_time_ms=query_time,
            response_time_ms=response_time
        )
        
        return search_response
        
    except Exception as e:
        logger.error(
            "Error performing search",
            filters=request.filters.model_dump(),
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform search"
        )


@app.get("/stats", response_model=Dict[str, Any])
async def get_service_stats():
    """Get comprehensive service statistics."""
    uptime = time.time() - service_metrics['start_time']
    
    # Get cache stats
    cache_stats = await cache_manager.get_cache_stats()
    
    # Get OpenSearch stats
    search_stats = await opensearch_client.get_search_stats()
    
    return {
        "service": {
            "name": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "uptime_seconds": uptime,
            "debug_mode": settings.DEBUG
        },
        "requests": {
            "parse_requests": service_metrics['parse_requests'],
            "search_requests": service_metrics['search_requests'],
            "error_count": service_metrics['error_count'],
            "requests_per_minute": (
                (service_metrics['parse_requests'] + service_metrics['search_requests']) / 
                (uptime / 60) if uptime > 0 else 0
            )
        },
        "cache": cache_stats,
        "search": search_stats,
        "rate_limiting": {
            "enabled": settings.RATE_LIMIT_ENABLED,
            "parse_limit": settings.PARSE_RATE_LIMIT,
            "search_limit": settings.SEARCH_RATE_LIMIT
        }
    }


@app.post("/cache/clear")
async def clear_cache():
    """Clear all cache entries (admin endpoint)."""
    success = await cache_manager.clear_cache()
    
    if success:
        logger.info("Cache cleared successfully")
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    ) 