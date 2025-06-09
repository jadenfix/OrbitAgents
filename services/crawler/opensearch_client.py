"""
OpenSearch Client for Listings Indexing
Handles creating indexes, mapping, and bulk indexing operations for MLS listings.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from opensearchpy import OpenSearch, AsyncOpenSearch
from opensearchpy.exceptions import (
    OpenSearchException, 
    ConnectionError as OSConnectionError,
    NotFoundError,
    RequestError
)
import structlog

from config import settings
from schemas import OpenSearchListing, NormalizedListing

logger = structlog.get_logger(__name__)


class OpenSearchClient:
    """
    OpenSearch client for indexing and searching MLS listings.
    Handles index creation, mapping, and bulk operations with retry logic.
    """
    
    def __init__(self):
        self.client = None
        self.async_client = None
        self.index_name = settings.opensearch_index
        self._index_created = False
        self._setup_clients()
    
    def _setup_clients(self):
        """Initialize OpenSearch clients with proper configuration."""
        try:
            # Client configuration
            client_config = {
                'hosts': [{'host': settings.opensearch_host, 'port': settings.opensearch_port}],
                'http_compress': True,
                'http_auth': None,
                'use_ssl': settings.opensearch_scheme == 'https',
                'verify_certs': settings.opensearch_scheme == 'https',
                'timeout': settings.opensearch_timeout,
                'max_retries': settings.opensearch_max_retries,
                'retry_on_timeout': True
            }
            
            # Add authentication if provided
            if settings.opensearch_username and settings.opensearch_password:
                client_config['http_auth'] = (
                    settings.opensearch_username, 
                    settings.opensearch_password
                )
            
            # Initialize synchronous client
            self.client = OpenSearch(**client_config)
            
            # Initialize asynchronous client
            self.async_client = AsyncOpenSearch(**client_config)
            
            logger.info(
                "OpenSearch clients initialized",
                host=settings.opensearch_host,
                port=settings.opensearch_port,
                index=self.index_name
            )
            
        except Exception as e:
            logger.error("Failed to initialize OpenSearch clients", error=str(e))
            raise
    
    async def initialize_index(self, force_recreate: bool = False) -> bool:
        """
        Create the listings index with proper mapping if it doesn't exist.
        
        Args:
            force_recreate: Whether to delete and recreate the index if it exists
            
        Returns:
            True if index was created/updated successfully
        """
        try:
            # Check if index exists
            index_exists = await self.async_client.indices.exists(index=self.index_name)
            
            if index_exists and force_recreate:
                logger.info("Deleting existing index", index=self.index_name)
                await self.async_client.indices.delete(index=self.index_name)
                index_exists = False
            
            if not index_exists:
                # Create index with mapping
                mapping = self._get_listings_mapping()
                settings_config = self._get_index_settings()
                
                create_body = {
                    'settings': settings_config,
                    'mappings': mapping
                }
                
                await self.async_client.indices.create(
                    index=self.index_name,
                    body=create_body
                )
                
                logger.info(
                    "Created OpenSearch index",
                    index=self.index_name,
                    mapping=mapping,
                    settings=settings_config
                )
            else:
                logger.info("OpenSearch index already exists", index=self.index_name)
            
            self._index_created = True
            return True
            
        except RequestError as e:
            if "resource_already_exists_exception" in str(e):
                logger.info("Index already exists", index=self.index_name)
                self._index_created = True
                return True
            else:
                logger.error("Failed to create OpenSearch index", error=str(e))
                return False
        except Exception as e:
            logger.error("Failed to initialize OpenSearch index", error=str(e))
            return False
    
    async def index_listing(self, listing: NormalizedListing) -> bool:
        """
        Index a single listing document.
        
        Args:
            listing: Normalized listing to index
            
        Returns:
            True if indexed successfully
        """
        try:
            if not self._index_created:
                await self.initialize_index()
            
            # Convert to OpenSearch document
            doc = OpenSearchListing.from_normalized_listing(listing)
            doc_dict = doc.model_dump()
            
            # Index the document
            await self.async_client.index(
                index=self.index_name,
                id=listing.mls_id,
                body=doc_dict,
                refresh=False  # Don't refresh immediately for performance
            )
            
            logger.debug(
                "Indexed listing in OpenSearch",
                mls_id=listing.mls_id,
                index=self.index_name
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to index listing",
                error=str(e),
                mls_id=listing.mls_id
            )
            return False
    
    async def bulk_index_listings(self, listings: List[NormalizedListing]) -> Dict[str, int]:
        """
        Index multiple listings in bulk for better performance.
        
        Args:
            listings: List of normalized listings to index
            
        Returns:
            Dictionary with statistics: {'indexed': int, 'failed': int, 'errors': []}
        """
        if not listings:
            return {'indexed': 0, 'failed': 0, 'errors': []}
        
        try:
            if not self._index_created:
                await self.initialize_index()
            
            # Prepare bulk operations
            bulk_ops = []
            for listing in listings:
                doc = OpenSearchListing.from_normalized_listing(listing)
                doc_dict = doc.model_dump()
                
                # Add index operation
                bulk_ops.append({
                    'index': {
                        '_index': self.index_name,
                        '_id': listing.mls_id
                    }
                })
                bulk_ops.append(doc_dict)
            
            # Execute bulk operation
            response = await self.async_client.bulk(
                body=bulk_ops,
                refresh=False,
                request_timeout=60
            )
            
            # Process response
            stats = self._process_bulk_response(response)
            
            logger.info(
                "Bulk indexed listings",
                total_listings=len(listings),
                indexed=stats['indexed'],
                failed=stats['failed'],
                index=self.index_name
            )
            
            if stats['errors']:
                logger.warning(
                    "Bulk index errors",
                    error_count=len(stats['errors']),
                    sample_errors=stats['errors'][:5]  # Log first 5 errors
                )
            
            return stats
            
        except Exception as e:
            logger.error(
                "Failed to bulk index listings",
                error=str(e),
                listing_count=len(listings)
            )
            return {
                'indexed': 0, 
                'failed': len(listings), 
                'errors': [{'error': str(e), 'type': 'bulk_operation_failed'}]
            }
    
    async def search_listings(
        self,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Search listings using OpenSearch query DSL.
        
        Args:
            query: OpenSearch query DSL
            size: Number of results to return
            from_: Starting offset
            sort: Sort configuration
            
        Returns:
            Search response with hits and metadata
        """
        try:
            search_body = {
                'query': query,
                'size': size,
                'from': from_
            }
            
            if sort:
                search_body['sort'] = sort
            
            response = await self.async_client.search(
                index=self.index_name,
                body=search_body
            )
            
            return response
            
        except Exception as e:
            logger.error("Failed to search listings", error=str(e), query=query)
            raise
    
    async def delete_listing(self, mls_id: str) -> bool:
        """
        Delete a listing from the index.
        
        Args:
            mls_id: MLS ID of the listing to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            await self.async_client.delete(
                index=self.index_name,
                id=mls_id
            )
            
            logger.debug("Deleted listing from OpenSearch", mls_id=mls_id)
            return True
            
        except NotFoundError:
            logger.warning("Listing not found for deletion", mls_id=mls_id)
            return False
        except Exception as e:
            logger.error("Failed to delete listing", error=str(e), mls_id=mls_id)
            return False
    
    async def refresh_index(self):
        """Force index refresh to make documents searchable immediately."""
        try:
            await self.async_client.indices.refresh(index=self.index_name)
            logger.debug("Refreshed OpenSearch index", index=self.index_name)
        except Exception as e:
            logger.error("Failed to refresh index", error=str(e))
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        try:
            stats = await self.async_client.indices.stats(index=self.index_name)
            
            index_stats = stats['indices'][self.index_name]
            return {
                'document_count': index_stats['total']['docs']['count'],
                'document_deleted': index_stats['total']['docs']['deleted'],
                'store_size_bytes': index_stats['total']['store']['size_in_bytes'],
                'index_name': self.index_name
            }
            
        except Exception as e:
            logger.error("Failed to get index stats", error=str(e))
            return {}
    
    async def health_check(self) -> bool:
        """
        Check OpenSearch cluster health.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            health = await self.async_client.cluster.health()
            status = health.get('status', 'red')
            
            if status in ['green', 'yellow']:
                return True
            else:
                logger.warning("OpenSearch cluster unhealthy", status=status)
                return False
                
        except Exception as e:
            logger.error("OpenSearch health check failed", error=str(e))
            return False
    
    async def close(self):
        """Close OpenSearch connections."""
        try:
            if self.async_client:
                await self.async_client.close()
            logger.info("OpenSearch connections closed")
        except Exception as e:
            logger.error("Error closing OpenSearch connections", error=str(e))
    
    def _get_listings_mapping(self) -> Dict[str, Any]:
        """
        Get the OpenSearch mapping configuration for listings index.
        Optimized for search and geographic queries.
        """
        return {
            'properties': {
                'mls_id': {
                    'type': 'keyword',
                    'index': True
                },
                'beds': {
                    'type': 'integer'
                },
                'baths': {
                    'type': 'float'
                },
                'price': {
                    'type': 'long'
                },
                'location': {
                    'type': 'geo_point'
                },
                'property_type': {
                    'type': 'keyword',
                    'index': True
                },
                'status': {
                    'type': 'keyword',
                    'index': True
                },
                'square_feet': {
                    'type': 'integer'
                },
                'year_built': {
                    'type': 'integer'
                },
                'city': {
                    'type': 'keyword',
                    'index': True,
                    'fields': {
                        'text': {
                            'type': 'text',
                            'analyzer': 'standard'
                        }
                    }
                },
                'state': {
                    'type': 'keyword',
                    'index': True
                },
                'zip_code': {
                    'type': 'keyword',
                    'index': True
                },
                'description': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {
                            'type': 'keyword',
                            'ignore_above': 256
                        }
                    }
                },
                'crawled_at': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                },
                'last_updated': {
                    'type': 'date',
                    'format': 'strict_date_optional_time||epoch_millis'
                }
            }
        }
    
    def _get_index_settings(self) -> Dict[str, Any]:
        """Get the OpenSearch index settings configuration."""
        return {
            'number_of_shards': 1,
            'number_of_replicas': 0,  # Can be increased in production
            'refresh_interval': '30s',  # Batch refresh for better performance
            'analysis': {
                'analyzer': {
                    'standard': {
                        'type': 'standard',
                        'stopwords': '_english_'
                    }
                }
            }
        }
    
    def _process_bulk_response(self, response: Dict[str, Any]) -> Dict[str, int]:
        """Process bulk operation response and extract statistics."""
        stats = {'indexed': 0, 'failed': 0, 'errors': []}
        
        for item in response.get('items', []):
            if 'index' in item:
                index_result = item['index']
                if index_result.get('status') in [200, 201]:
                    stats['indexed'] += 1
                else:
                    stats['failed'] += 1
                    if 'error' in index_result:
                        stats['errors'].append({
                            'id': index_result.get('_id'),
                            'error': index_result['error'],
                            'status': index_result.get('status')
                        })
        
        return stats


# Global OpenSearch client instance
opensearch_client = OpenSearchClient() 