"""
S3 Storage Manager
Handles uploading and retrieving raw MLS data to/from S3 with comprehensive error handling.
"""

import json
import gzip
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from io import BytesIO
import asyncio
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import structlog

from config import settings

logger = structlog.get_logger(__name__)


class S3Manager:
    """
    S3 client wrapper for storing raw MLS data with compression and metadata.
    Implements retry logic and error handling for production use.
    """
    
    def __init__(self):
        self.client = None
        self.bucket_name = settings.s3_bucket
        self._initialized = False
        self._setup_client()
    
    def _setup_client(self):
        """Initialize S3 client with proper configuration."""
        try:
            # Configure boto3 with retry settings
            config = Config(
                region_name=settings.s3_region,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                max_pool_connections=50
            )
            
            # Initialize client with optional credentials
            if settings.s3_access_key_id and settings.s3_secret_access_key:
                self.client = boto3.client(
                    's3',
                    aws_access_key_id=settings.s3_access_key_id,
                    aws_secret_access_key=settings.s3_secret_access_key,
                    endpoint_url=settings.s3_endpoint_url,
                    config=config
                )
            else:
                # Use IAM role or environment credentials
                self.client = boto3.client(
                    's3',
                    endpoint_url=settings.s3_endpoint_url,
                    config=config
                )
            
            logger.info("S3 client initialized", 
                       bucket=self.bucket_name, 
                       region=settings.s3_region)
            
        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise
        except Exception as e:
            logger.error("Failed to initialize S3 client", error=str(e))
            raise
    
    async def store_raw_data(
        self, 
        data: List[Dict[str, Any]], 
        timestamp: Optional[datetime] = None,
        compress: bool = True,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Store raw MLS data in S3 with compression and metadata.
        
        Args:
            data: List of raw MLS listing dictionaries
            timestamp: Timestamp for the data (defaults to current time)
            compress: Whether to compress the data with gzip
            metadata: Additional metadata to store with the object
            
        Returns:
            S3 key of the stored object
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Generate S3 key with hierarchical structure
        key = self._generate_s3_key(timestamp)
        
        try:
            # Prepare data for storage
            json_data = json.dumps(data, default=str, separators=(',', ':'))
            
            # Compress if requested
            if compress:
                buffer = BytesIO()
                with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
                    gz_file.write(json_data.encode('utf-8'))
                content = buffer.getvalue()
                content_type = 'application/gzip'
                content_encoding = 'gzip'
            else:
                content = json_data.encode('utf-8')
                content_type = 'application/json'
                content_encoding = None
            
            # Prepare metadata
            object_metadata = {
                'crawl-timestamp': timestamp.isoformat(),
                'record-count': str(len(data)),
                'data-format': 'json',
                'service': 'orbit-crawler'
            }
            if metadata:
                object_metadata.update(metadata)
            
            # Upload to S3
            await self._upload_with_retry(
                key=key,
                content=content,
                content_type=content_type,
                content_encoding=content_encoding,
                metadata=object_metadata
            )
            
            logger.info(
                "Raw data stored to S3",
                s3_key=key,
                record_count=len(data),
                compressed=compress,
                size_bytes=len(content)
            )
            
            return key
            
        except Exception as e:
            logger.error("Failed to store raw data to S3", error=str(e), s3_key=key)
            raise
    
    async def retrieve_raw_data(self, s3_key: str) -> List[Dict[str, Any]]:
        """
        Retrieve and decompress raw MLS data from S3.
        
        Args:
            s3_key: S3 key of the object to retrieve
            
        Returns:
            List of raw MLS listing dictionaries
        """
        try:
            # Download object
            response = await self._download_with_retry(s3_key)
            content = response['Body'].read()
            
            # Check if compressed
            if response.get('ContentEncoding') == 'gzip':
                content = gzip.decompress(content)
            
            # Parse JSON
            data = json.loads(content.decode('utf-8'))
            
            logger.info(
                "Raw data retrieved from S3",
                s3_key=s3_key,
                record_count=len(data) if isinstance(data, list) else 1
            )
            
            return data if isinstance(data, list) else [data]
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning("S3 object not found", s3_key=s3_key)
                return []
            else:
                logger.error("S3 client error", error=str(e), s3_key=s3_key)
                raise
        except Exception as e:
            logger.error("Failed to retrieve raw data from S3", error=str(e), s3_key=s3_key)
            raise
    
    async def list_raw_data_keys(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[str]:
        """
        List S3 keys for raw data within a date range.
        
        Args:
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            limit: Maximum number of keys to return
            
        Returns:
            List of S3 keys
        """
        try:
            prefix = f"{settings.s3_raw_data_prefix}/"
            
            # Build date prefix if provided
            if start_date:
                date_prefix = start_date.strftime("%Y/%m/%d")
                prefix = f"{settings.s3_raw_data_prefix}/{date_prefix}"
            
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            keys = []
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        
                        # Filter by date range if specified
                        if self._key_in_date_range(key, start_date, end_date):
                            keys.append(key)
                        
                        if len(keys) >= limit:
                            break
                
                if len(keys) >= limit:
                    break
            
            logger.info(
                "Listed S3 keys",
                prefix=prefix,
                key_count=len(keys),
                start_date=start_date,
                end_date=end_date
            )
            
            return keys
            
        except Exception as e:
            logger.error("Failed to list S3 keys", error=str(e), prefix=prefix)
            raise
    
    async def delete_raw_data(self, s3_key: str) -> bool:
        """
        Delete raw data object from S3.
        
        Args:
            s3_key: S3 key of the object to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            await self._delete_with_retry(s3_key)
            logger.info("Raw data deleted from S3", s3_key=s3_key)
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning("S3 object not found for deletion", s3_key=s3_key)
                return False
            else:
                logger.error("Failed to delete S3 object", error=str(e), s3_key=s3_key)
                return False
        except Exception as e:
            logger.error("Failed to delete raw data from S3", error=str(e), s3_key=s3_key)
            return False
    
    async def health_check(self) -> bool:
        """
        Check S3 connectivity and bucket access.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to list objects with minimal prefix
            self.client.list_objects_v2(
                Bucket=self.bucket_name,
                MaxKeys=1
            )
            return True
            
        except Exception as e:
            logger.error("S3 health check failed", error=str(e))
            return False
    
    def _generate_s3_key(self, timestamp: datetime) -> str:
        """
        Generate hierarchical S3 key for raw data storage.
        Format: raw/YYYY/MM/DD/HH/YYYYMMDD_HHMMSS_<uuid>.json.gz
        """
        import uuid
        
        date_part = timestamp.strftime("%Y/%m/%d/%H")
        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
        
        if settings.s3_raw_data_prefix:
            return f"{settings.s3_raw_data_prefix}/{date_part}/{filename}"
        else:
            return f"{date_part}/{filename}"
    
    def _key_in_date_range(
        self, 
        key: str, 
        start_date: Optional[datetime], 
        end_date: Optional[datetime]
    ) -> bool:
        """Check if S3 key falls within the specified date range."""
        if not start_date and not end_date:
            return True
        
        try:
            # Extract date from key format: raw/YYYY/MM/DD/HH/filename
            parts = key.split('/')
            if len(parts) >= 5:
                year, month, day, hour = parts[1:5]
                key_date = datetime(
                    int(year), int(month), int(day), int(hour),
                    tzinfo=timezone.utc
                )
                
                if start_date and key_date < start_date:
                    return False
                if end_date and key_date > end_date:
                    return False
                
                return True
        except (ValueError, IndexError):
            # If we can't parse the date, include the key
            pass
        
        return True
    
    async def _upload_with_retry(
        self,
        key: str,
        content: bytes,
        content_type: str,
        content_encoding: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ):
        """Upload to S3 with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                put_args = {
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'Body': content,
                    'ContentType': content_type,
                }
                
                if content_encoding:
                    put_args['ContentEncoding'] = content_encoding
                
                if metadata:
                    put_args['Metadata'] = metadata
                
                self.client.put_object(**put_args)
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "S3 upload attempt failed, retrying",
                        attempt=attempt + 1,
                        error=str(e),
                        s3_key=key
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    raise
    
    async def _download_with_retry(self, key: str) -> Dict[str, Any]:
        """Download from S3 with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                return self.client.get_object(Bucket=self.bucket_name, Key=key)
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "S3 download attempt failed, retrying",
                        attempt=attempt + 1,
                        error=str(e),
                        s3_key=key
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    raise
    
    async def _delete_with_retry(self, key: str):
        """Delete from S3 with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.client.delete_object(Bucket=self.bucket_name, Key=key)
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "S3 delete attempt failed, retrying",
                        attempt=attempt + 1,
                        error=str(e),
                        s3_key=key
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    raise


# Global S3 manager instance
s3_manager = S3Manager() 