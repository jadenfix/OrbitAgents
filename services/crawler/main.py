"""
Crawler Service FastAPI Application
REST API for MLS data crawler with health checks and manual triggers.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from config import settings
from schemas import CrawlJobStatus, HealthCheck
from mls_crawler import mls_crawler
from database import db_manager, get_db
from s3_manager import s3_manager
from opensearch_client import opensearch_client

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

logger = structlog.get_logger(__name__)

# FastAPI application
app = FastAPI(
    title="Orbit MLS Crawler Service",
    description="MLS data crawler for real estate listings with S3 storage and OpenSearch indexing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting Orbit MLS Crawler Service", version="1.0.0")
    
    try:
        # Initialize database
        await db_manager.initialize()
        
        # Initialize OpenSearch index
        await opensearch_client.initialize_index()
        
        logger.info("Crawler service started successfully")
        
    except Exception as e:
        logger.error("Failed to start crawler service", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown."""
    logger.info("Shutting down Orbit MLS Crawler Service")
    
    try:
        await mls_crawler.close()
        await db_manager.close()
        await opensearch_client.close()
        
        logger.info("Crawler service shut down successfully")
        
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Orbit MLS Crawler",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "crawl": "/crawl",
            "status": "/status/{job_id}",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Comprehensive health check for all service components.
    
    Returns:
        HealthCheck response with status of each component
    """
    logger.info("Performing health check")
    
    try:
        # Get health status from all components
        component_health = await mls_crawler.health_check()
        
        # Determine overall health
        all_healthy = all(component_health.values())
        
        health_response = HealthCheck(
            status="healthy" if all_healthy else "unhealthy",
            database_healthy=component_health.get('database', False),
            s3_healthy=component_health.get('s3', False),
            opensearch_healthy=component_health.get('opensearch', False),
            mls_api_healthy=component_health.get('mls_api', False)
        )
        
        # Get last crawl information from database
        try:
            async with db_manager.get_session() as db:
                from sqlalchemy import select, desc
                from database import CrawlJob
                
                result = await db.execute(
                    select(CrawlJob)
                    .order_by(desc(CrawlJob.created_at))
                    .limit(1)
                )
                last_job = result.scalar_one_or_none()
                
                if last_job:
                    health_response.last_crawl_at = last_job.started_at
                    health_response.last_crawl_status = last_job.status
                    
        except Exception as e:
            logger.warning("Could not retrieve last crawl info", error=str(e))
        
        status_code = 200 if all_healthy else 503
        
        logger.info(
            "Health check completed",
            overall_status=health_response.status,
            components=component_health
        )
        
        return JSONResponse(
            status_code=status_code,
            content=health_response.model_dump()
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        
        return JSONResponse(
            status_code=503,
            content=HealthCheck(
                status="unhealthy",
                database_healthy=False,
                s3_healthy=False,
                opensearch_healthy=False,
                mls_api_healthy=False
            ).model_dump()
        )


@app.post("/crawl", response_model=CrawlJobStatus)
async def trigger_crawl(background_tasks: BackgroundTasks):
    """
    Manually trigger a crawl job.
    
    Returns:
        CrawlJobStatus with job information
    """
    logger.info("Manual crawl job triggered")
    
    try:
        # Start crawl job in background
        job_status = await mls_crawler.run_crawl_job()
        
        logger.info("Crawl job completed", job_id=job_status.job_id, status=job_status.status)
        
        return job_status
        
    except Exception as e:
        logger.error("Failed to trigger crawl job", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger crawl job: {str(e)}"
        )


@app.get("/status/{job_id}", response_model=CrawlJobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a specific crawl job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        CrawlJobStatus with job details and statistics
    """
    logger.info("Retrieving job status", job_id=job_id)
    
    try:
        async with db_manager.get_session() as db:
            from sqlalchemy import select
            from database import CrawlJob
            
            result = await db.execute(
                select(CrawlJob).where(CrawlJob.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if not job:
                raise HTTPException(
                    status_code=404,
                    detail=f"Job {job_id} not found"
                )
            
            job_status = CrawlJobStatus(
                job_id=job.job_id,
                status=job.status,
                started_at=job.started_at,
                completed_at=job.completed_at,
                total_fetched=job.total_fetched,
                total_processed=job.total_processed,
                total_saved=job.total_saved,
                total_indexed=job.total_indexed,
                total_errors=job.total_errors,
                error_message=job.error_message,
                error_details=job.error_details
            )
            
            return job_status
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve job status", error=str(e), job_id=job_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve job status: {str(e)}"
        )


@app.get("/jobs", response_model=Dict[str, Any])
async def list_jobs(limit: int = 20, offset: int = 0):
    """
    List recent crawl jobs with pagination.
    
    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        
    Returns:
        Dictionary with jobs list and pagination info
    """
    logger.info("Listing crawl jobs", limit=limit, offset=offset)
    
    try:
        async with db_manager.get_session() as db:
            from sqlalchemy import select, desc, func
            from database import CrawlJob
            
            # Get total count
            count_result = await db.execute(select(func.count(CrawlJob.id)))
            total_count = count_result.scalar()
            
            # Get jobs with pagination
            result = await db.execute(
                select(CrawlJob)
                .order_by(desc(CrawlJob.created_at))
                .limit(limit)
                .offset(offset)
            )
            jobs = result.scalars().all()
            
            jobs_data = []
            for job in jobs:
                jobs_data.append({
                    "job_id": job.job_id,
                    "status": job.status,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "total_fetched": job.total_fetched,
                    "total_processed": job.total_processed,
                    "total_saved": job.total_saved,
                    "total_indexed": job.total_indexed,
                    "total_errors": job.total_errors
                })
            
            return {
                "jobs": jobs_data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list jobs: {str(e)}"
        )


@app.get("/stats", response_model=Dict[str, Any])
async def get_statistics():
    """
    Get crawler service statistics and metrics.
    
    Returns:
        Dictionary with various service statistics
    """
    logger.info("Retrieving service statistics")
    
    try:
        stats = {}
        
        # Database statistics
        async with db_manager.get_session() as db:
            from sqlalchemy import select, func
            from database import Listing, CrawlJob
            
            # Listing statistics
            listing_count = await db.execute(select(func.count(Listing.id)))
            stats['total_listings'] = listing_count.scalar()
            
            active_listings = await db.execute(
                select(func.count(Listing.id)).where(Listing.is_active == True)
            )
            stats['active_listings'] = active_listings.scalar()
            
            # Job statistics
            job_count = await db.execute(select(func.count(CrawlJob.id)))
            stats['total_jobs'] = job_count.scalar()
            
            successful_jobs = await db.execute(
                select(func.count(CrawlJob.id)).where(CrawlJob.status == 'completed')
            )
            stats['successful_jobs'] = successful_jobs.scalar()
            
            failed_jobs = await db.execute(
                select(func.count(CrawlJob.id)).where(CrawlJob.status == 'failed')
            )
            stats['failed_jobs'] = failed_jobs.scalar()
        
        # OpenSearch statistics
        try:
            opensearch_stats = await opensearch_client.get_index_stats()
            stats['opensearch'] = opensearch_stats
        except Exception as e:
            logger.warning("Could not retrieve OpenSearch stats", error=str(e))
            stats['opensearch'] = {}
        
        # Service configuration
        stats['configuration'] = {
            'batch_size': settings.batch_size,
            'max_listings_per_run': settings.max_listings_per_run,
            'mls_retry_attempts': settings.mls_retry_attempts,
            'scheduler_enabled': settings.enable_scheduler
        }
        
        stats['timestamp'] = datetime.utcnow().isoformat()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to retrieve statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@app.get("/metrics")
async def get_metrics():
    """
    Get Prometheus-style metrics for monitoring.
    
    Returns:
        Plain text metrics in Prometheus format
    """
    try:
        metrics = []
        
        # Get basic statistics
        async with db_manager.get_session() as db:
            from sqlalchemy import select, func
            from database import Listing, CrawlJob
            
            listing_count = await db.execute(select(func.count(Listing.id)))
            total_listings = listing_count.scalar()
            
            job_count = await db.execute(select(func.count(CrawlJob.id)))
            total_jobs = job_count.scalar()
        
        # Format as Prometheus metrics
        metrics.append(f"crawler_total_listings {total_listings}")
        metrics.append(f"crawler_total_jobs {total_jobs}")
        metrics.append(f"crawler_service_up 1")
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error("Failed to generate metrics", error=str(e))
        return "crawler_service_up 0"


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 