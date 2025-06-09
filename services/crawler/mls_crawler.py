"""
MLS Data Crawler
Main crawler logic for fetching, processing, and indexing MLS listing data.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from config import settings
from schemas import (
    MLSRawListing, MLSApiResponse, NormalizedListing, 
    CrawlJobStatus, PropertyType, ListingStatus
)
from database import db_manager, get_db, Listing, CrawlJob
from s3_manager import s3_manager
from opensearch_client import opensearch_client

logger = structlog.get_logger(__name__)


class MLSCrawler:
    """MLS data crawler with comprehensive error handling and retry logic."""
    
    def __init__(self):
        self.http_client = None
        self._setup_http_client()
    
    def _setup_http_client(self):
        """Initialize HTTP client with proper configuration."""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.mls_timeout),
            headers={
                'User-Agent': 'OrbitCrawler/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        
        # Add API key if configured
        if settings.mls_api_key:
            self.http_client.headers['Authorization'] = f'Bearer {settings.mls_api_key}'
    
    async def run_crawl_job(self) -> CrawlJobStatus:
        """Execute a complete crawl job: fetch, store, normalize, and index."""
        job_id = f"crawl_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        job_status = CrawlJobStatus(
            job_id=job_id,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        
        logger.info("Starting crawl job", job_id=job_id)
        
        try:
            # Initialize services
            await self._initialize_services()
            
            # Create job tracking record
            async with db_manager.get_session() as db:
                await self._create_job_record(db, job_status)
            
            # Step 1: Fetch raw MLS data
            raw_listings = await self._fetch_mls_data()
            job_status.total_fetched = len(raw_listings)
            
            if not raw_listings:
                logger.warning("No listings fetched from MLS API")
                job_status.status = "completed"
                job_status.completed_at = datetime.now(timezone.utc)
                return job_status
            
            # Step 2: Store raw data to S3
            s3_key = await self._store_raw_data(raw_listings)
            
            # Step 3: Process and normalize listings
            normalized_listings = await self._normalize_listings(raw_listings, s3_key)
            job_status.total_processed = len(normalized_listings)
            
            # Step 4: Save to database
            saved_count = await self._save_to_database(normalized_listings)
            job_status.total_saved = saved_count
            
            # Step 5: Index in OpenSearch
            indexed_count = await self._index_in_opensearch(normalized_listings)
            job_status.total_indexed = indexed_count
            
            # Mark job as completed
            job_status.status = "completed"
            job_status.completed_at = datetime.now(timezone.utc)
            
            logger.info(
                "Crawl job completed successfully",
                job_id=job_id,
                fetched=job_status.total_fetched,
                processed=job_status.total_processed,
                saved=job_status.total_saved,
                indexed=job_status.total_indexed
            )
            
        except Exception as e:
            job_status.status = "failed"
            job_status.completed_at = datetime.now(timezone.utc)
            job_status.error_message = str(e)
            job_status.error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e)
            }
            
            logger.error("Crawl job failed", job_id=job_id, error=str(e))
            
        finally:
            # Update job record
            async with db_manager.get_session() as db:
                await self._update_job_record(db, job_status)
        
        return job_status
    
    async def _fetch_mls_data(self) -> List[Dict[str, Any]]:
        """Fetch raw listing data from MLS API with retry logic."""
        logger.info("Fetching data from MLS API", api_url=settings.mls_api_url)
        
        for attempt in range(settings.mls_retry_attempts):
            try:
                response = await self.http_client.get(
                    settings.mls_api_url,
                    params={'limit': settings.max_listings_per_run}
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Handle different API response formats
                if isinstance(data, list):
                    listings = data
                elif isinstance(data, dict):
                    if 'listings' in data:
                        listings = data['listings']
                    elif 'data' in data:
                        listings = data['data']
                    else:
                        listings = [data]
                else:
                    listings = []
                
                logger.info("Successfully fetched MLS data", listing_count=len(listings))
                return listings
                
            except Exception as e:
                logger.warning(f"MLS API attempt {attempt + 1} failed", error=str(e))
                if attempt < settings.mls_retry_attempts - 1:
                    await asyncio.sleep(settings.mls_retry_delay * (2 ** attempt))
                else:
                    raise
        
        return []
    
    async def _store_raw_data(self, listings: List[Dict[str, Any]]) -> str:
        """Store raw listing data to S3 with compression."""
        logger.info("Storing raw data to S3", listing_count=len(listings))
        
        metadata = {
            'source': 'mls_api',
            'api_url': settings.mls_api_url,
            'crawler_version': '1.0'
        }
        
        s3_key = await s3_manager.store_raw_data(
            data=listings,
            compress=True,
            metadata=metadata
        )
        
        logger.info("Raw data stored to S3", s3_key=s3_key)
        return s3_key
    
    async def _normalize_listings(
        self, 
        raw_listings: List[Dict[str, Any]], 
        s3_key: str
    ) -> List[NormalizedListing]:
        """Normalize raw MLS data into structured format."""
        logger.info("Normalizing listings", listing_count=len(raw_listings))
        
        normalized = []
        errors = 0
        
        for raw_data in raw_listings:
            try:
                # Parse raw listing with validation
                mls_listing = MLSRawListing(**raw_data)
                
                # Convert to normalized format
                normalized_listing = NormalizedListing.from_mls_listing(
                    mls_listing, 
                    s3_key=s3_key
                )
                
                normalized.append(normalized_listing)
                
            except Exception as e:
                errors += 1
                logger.warning("Failed to normalize listing", error=str(e))
                
                if errors > len(raw_listings) * 0.1:  # More than 10% errors
                    logger.error("Too many normalization errors, stopping")
                    break
        
        logger.info(
            "Listings normalized",
            total_input=len(raw_listings),
            normalized_count=len(normalized),
            error_count=errors
        )
        
        return normalized
    
    async def _save_to_database(self, listings: List[NormalizedListing]) -> int:
        """Save normalized listings to PostgreSQL database with upsert logic."""
        logger.info("Saving listings to database", listing_count=len(listings))
        
        saved_count = 0
        
        async with db_manager.get_session() as db:
            for batch_start in range(0, len(listings), settings.batch_size):
                batch = listings[batch_start:batch_start + settings.batch_size]
                
                try:
                    for listing in batch:
                        # Check if listing already exists
                        existing = await db.execute(
                            select(Listing).where(Listing.mls_id == listing.mls_id)
                        )
                        existing_listing = existing.scalar_one_or_none()
                        
                        if existing_listing:
                            # Update existing listing
                            update_data = {
                                'beds': listing.beds,
                                'baths': listing.baths,
                                'price': listing.price,
                                'latitude': listing.latitude,
                                'longitude': listing.longitude,
                                'property_type': listing.property_type.value if listing.property_type else None,
                                'status': listing.status.value if listing.status else None,
                                'square_feet': listing.square_feet,
                                'crawled_at': listing.crawled_at,
                                'updated_at': datetime.now(timezone.utc)
                            }
                            
                            await db.execute(
                                update(Listing)
                                .where(Listing.mls_id == listing.mls_id)
                                .values(**update_data)
                            )
                        else:
                            # Insert new listing
                            db_listing = Listing(
                                mls_id=listing.mls_id,
                                beds=listing.beds,
                                baths=listing.baths,
                                price=listing.price,
                                latitude=listing.latitude,
                                longitude=listing.longitude,
                                property_type=listing.property_type.value if listing.property_type else None,
                                status=listing.status.value if listing.status else None,
                                square_feet=listing.square_feet,
                                crawled_at=listing.crawled_at,
                                raw_data_s3_key=listing.raw_data_s3_key
                            )
                            db.add(db_listing)
                        
                        saved_count += 1
                    
                    # Commit batch
                    await db.commit()
                    
                except Exception as e:
                    await db.rollback()
                    logger.error("Failed to save batch", error=str(e))
        
        logger.info("Listings saved to database", saved_count=saved_count)
        return saved_count
    
    async def _index_in_opensearch(self, listings: List[NormalizedListing]) -> int:
        """Index normalized listings in OpenSearch."""
        logger.info("Indexing listings in OpenSearch", listing_count=len(listings))
        
        # Initialize index if needed
        await opensearch_client.initialize_index()
        
        # Index in batches for better performance
        total_indexed = 0
        
        for batch_start in range(0, len(listings), settings.batch_size):
            batch = listings[batch_start:batch_start + settings.batch_size]
            
            try:
                stats = await opensearch_client.bulk_index_listings(batch)
                total_indexed += stats['indexed']
                
            except Exception as e:
                logger.error("Failed to index batch", error=str(e))
        
        # Refresh index to make documents searchable
        await opensearch_client.refresh_index()
        
        logger.info("Listings indexed in OpenSearch", indexed_count=total_indexed)
        return total_indexed
    
    async def _initialize_services(self):
        """Initialize all required services."""
        if not db_manager._initialized:
            await db_manager.initialize()
        
        await opensearch_client.initialize_index()
        
        logger.info("Services initialized")
    
    async def _create_job_record(self, db: AsyncSession, job_status: CrawlJobStatus):
        """Create a job tracking record in the database."""
        job_record = CrawlJob(
            job_id=job_status.job_id,
            status=job_status.status,
            started_at=job_status.started_at,
            config_snapshot={
                'mls_api_url': settings.mls_api_url,
                'batch_size': settings.batch_size,
                'max_listings_per_run': settings.max_listings_per_run
            }
        )
        
        db.add(job_record)
        await db.commit()
    
    async def _update_job_record(self, db: AsyncSession, job_status: CrawlJobStatus):
        """Update the job tracking record with final statistics."""
        try:
            await db.execute(
                update(CrawlJob)
                .where(CrawlJob.job_id == job_status.job_id)
                .values(
                    status=job_status.status,
                    completed_at=job_status.completed_at,
                    total_fetched=job_status.total_fetched,
                    total_processed=job_status.total_processed,
                    total_saved=job_status.total_saved,
                    total_indexed=job_status.total_indexed,
                    total_errors=job_status.total_errors,
                    error_message=job_status.error_message,
                    error_details=job_status.error_details
                )
            )
            await db.commit()
            
        except Exception as e:
            logger.error("Failed to update job record", error=str(e))
    
    async def health_check(self) -> Dict[str, bool]:
        """Perform health checks on all components."""
        health = {}
        
        # Check MLS API
        try:
            response = await self.http_client.head(settings.mls_api_url, timeout=5)
            health['mls_api'] = response.status_code < 500
        except:
            health['mls_api'] = False
        
        # Check database
        health['database'] = await db_manager.health_check()
        
        # Check S3
        health['s3'] = await s3_manager.health_check()
        
        # Check OpenSearch
        health['opensearch'] = await opensearch_client.health_check()
        
        return health
    
    async def close(self):
        """Clean up resources."""
        if self.http_client:
            await self.http_client.aclose()
        
        await db_manager.close()
        await opensearch_client.close()


# Global crawler instance
mls_crawler = MLSCrawler() 