"""
OpenSearch client for property search with comprehensive query building,
error handling, and connection management.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone

try:
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from opensearchpy.exceptions import (
        OpenSearchException, ConnectionError, AuthenticationException,
        NotFoundError, RequestError, TransportError
    )
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    logging.warning("OpenSearch not available. Search functionality will be limited.")

from config import settings
from schemas import SearchFilters, PropertyListing, GeoPoint

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """
    OpenSearch client with comprehensive error handling and query building capabilities.
    """
    
    def __init__(self):
        """Initialize OpenSearch client with connection management."""
        self.client: Optional[OpenSearch] = None
        self.is_connected = False
        self.last_health_check = 0
        self.health_check_interval = 60  # seconds
        
        # Query metrics
        self.search_count = 0
        self.error_count = 0
        self.total_query_time = 0.0
    
    async def initialize(self) -> bool:
        """Initialize OpenSearch connection with error handling."""
        if not OPENSEARCH_AVAILABLE:
            logger.warning("OpenSearch client not available")
            return False
            
        try:
            # Parse OpenSearch URL
            url_parts = settings.OPENSEARCH_URL.replace('https://', '').replace('http://', '')
            host_port = url_parts.split(':')
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else (443 if 'https' in settings.OPENSEARCH_URL else 9200)
            
            # Create client configuration
            client_config = {
                'hosts': [{'host': host, 'port': port}],
                'http_auth': (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD),
                'use_ssl': 'https' in settings.OPENSEARCH_URL,
                'verify_certs': settings.OPENSEARCH_VERIFY_CERTS,
                'ssl_show_warn': False,
                'connection_class': RequestsHttpConnection,
                'timeout': 30,
                'max_retries': 3,
                'retry_on_timeout': True,
                'http_compress': True,
            }
            
            # Create client
            self.client = OpenSearch(**client_config)
            
            # Test connection
            cluster_info = self.client.info()
            self.is_connected = True
            self.last_health_check = time.time()
            
            logger.info(f"Connected to OpenSearch cluster: {cluster_info.get('cluster_name', 'unknown')}")
            
            # Ensure index exists
            await self._ensure_index_exists()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OpenSearch: {e}")
            self.is_connected = False
            return False
    
    async def _ensure_index_exists(self) -> bool:
        """Ensure the listings index exists with proper mapping."""
        if not self.client:
            return False
            
        try:
            index_name = settings.OPENSEARCH_INDEX
            
            # Check if index exists
            if self.client.indices.exists(index=index_name):
                logger.debug(f"Index {index_name} already exists")
                return True
            
            # Create index with mapping
            mapping = self._get_index_mapping()
            self.client.indices.create(
                index=index_name,
                body={
                    'mappings': mapping,
                    'settings': {
                        'number_of_shards': 1,
                        'number_of_replicas': 0,
                        'index.mapping.total_fields.limit': 2000,
                    }
                }
            )
            
            logger.info(f"Created index {index_name} with mapping")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure index exists: {e}")
            return False
    
    def _get_index_mapping(self) -> Dict[str, Any]:
        """Get the OpenSearch index mapping for property listings."""
        return {
            'properties': {
                'id': {'type': 'keyword'},
                'price': {'type': 'float'},
                'beds': {'type': 'integer'},
                'baths': {'type': 'float'},
                'location': {'type': 'geo_point'},
                'address': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
                'city': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
                'neighborhood': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
                'property_type': {'type': 'keyword'},
                'title': {'type': 'text'},
                'description': {'type': 'text'},
                'amenities': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
                'images': {'type': 'keyword'},
                'date_added': {'type': 'date'},
                'date_updated': {'type': 'date'},
                'has_parking': {'type': 'boolean'},
                'has_pets': {'type': 'boolean'},
                'has_furnished': {'type': 'boolean'},
            }
        }
    
    async def health_check(self) -> bool:
        """Check OpenSearch cluster health."""
        if not OPENSEARCH_AVAILABLE or not self.client:
            return False
            
        current_time = time.time()
        
        # Skip if we checked recently
        if current_time - self.last_health_check < self.health_check_interval:
            return self.is_connected
        
        self.last_health_check = current_time
        
        try:
            health = self.client.cluster.health()
            cluster_status = health.get('status', 'red')
            
            if cluster_status in ['green', 'yellow']:
                if not self.is_connected:
                    logger.info("OpenSearch connection restored")
                    self.is_connected = True
                return True
            else:
                logger.warning(f"OpenSearch cluster status: {cluster_status}")
                self.is_connected = False
                return False
                
        except Exception as e:
            if self.is_connected:
                logger.warning(f"OpenSearch health check failed: {e}")
                self.is_connected = False
            return False
    
    async def search_properties(self, filters: SearchFilters, limit: int = 10, 
                              offset: int = 0, sort_by: str = "relevance", 
                              sort_order: str = "desc") -> Tuple[List[Dict[str, Any]], int, float]:
        """Search properties with comprehensive filtering and error handling."""
        if not await self.health_check():
            # Return empty results if OpenSearch unavailable
            logger.warning("OpenSearch unavailable, returning empty results")
            return [], 0, 0.0
        
        start_time = time.time()
        
        try:
            # Build search query
            query = self._build_search_query(filters)
            
            # Build sort configuration
            sort_config = self._build_sort_config(sort_by, sort_order, filters.location)
            
            # Execute search
            search_body = {
                'query': query,
                'size': min(limit, settings.MAX_SEARCH_LIMIT),
                'from': offset,
                'sort': sort_config,
                '_source': True,
                'track_total_hits': True
            }
            
            logger.debug(f"OpenSearch query: {json.dumps(search_body, indent=2)}")
            
            response = self.client.search(
                index=settings.OPENSEARCH_INDEX,
                body=search_body
            )
            
            # Process results
            results = []
            hits = response.get('hits', {}).get('hits', [])
            
            for hit in hits:
                try:
                    property_data = self._process_search_hit(hit)
                    if property_data:
                        results.append(property_data)
                except Exception as e:
                    logger.warning(f"Error processing search hit: {e}")
                    continue
            
            total_count = response.get('hits', {}).get('total', {}).get('value', 0)
            query_time = (time.time() - start_time) * 1000
            
            # Update metrics
            self.search_count += 1
            self.total_query_time += query_time
            
            logger.info(f"Search completed: {len(results)} results, {query_time:.1f}ms")
            
            return results, total_count, query_time
            
        except Exception as e:
            self.error_count += 1
            query_time = (time.time() - start_time) * 1000
            logger.error(f"Search error after {query_time:.1f}ms: {e}")
            return [], 0, query_time
    
    def _build_search_query(self, filters: SearchFilters) -> Dict[str, Any]:
        """Build OpenSearch query from search filters."""
        must_clauses = []
        filter_clauses = []
        should_clauses = []
        
        # Price filters
        if filters.price_min is not None or filters.price_max is not None:
            price_range = {}
            if filters.price_min is not None:
                price_range['gte'] = filters.price_min
            if filters.price_max is not None:
                price_range['lte'] = filters.price_max
            filter_clauses.append({'range': {'price': price_range}})
        
        # Bedroom filters
        if filters.beds is not None:
            filter_clauses.append({'term': {'beds': filters.beds}})
        elif filters.beds_min is not None or filters.beds_max is not None:
            beds_range = {}
            if filters.beds_min is not None:
                beds_range['gte'] = filters.beds_min
            if filters.beds_max is not None:
                beds_range['lte'] = filters.beds_max
            filter_clauses.append({'range': {'beds': beds_range}})
        
        # Bathroom filters
        if filters.baths is not None:
            filter_clauses.append({'term': {'baths': filters.baths}})
        elif filters.baths_min is not None or filters.baths_max is not None:
            baths_range = {}
            if filters.baths_min is not None:
                baths_range['gte'] = filters.baths_min
            if filters.baths_max is not None:
                baths_range['lte'] = filters.baths_max
            filter_clauses.append({'range': {'baths': baths_range}})
        
        # Property type filter
        if filters.property_type:
            filter_clauses.append({'term': {'property_type': filters.property_type.value}})
        
        # City filter
        if filters.city:
            should_clauses.extend([
                {'match': {'city': {'query': filters.city, 'boost': 2.0}}},
                {'match': {'city.keyword': {'query': filters.city, 'boost': 3.0}}}
            ])
        
        # Geographic filter
        if filters.location:
            radius = filters.radius or settings.DEFAULT_SEARCH_RADIUS
            filter_clauses.append({
                'geo_distance': {
                    'distance': radius,
                    'location': {
                        'lat': filters.location.lat,
                        'lon': filters.location.lon
                    }
                }
            })
        
        # Build final query
        if not must_clauses and not should_clauses:
            query = {'bool': {'filter': filter_clauses}} if filter_clauses else {'match_all': {}}
        else:
            bool_query = {}
            if must_clauses:
                bool_query['must'] = must_clauses
            if should_clauses:
                bool_query['should'] = should_clauses
                bool_query['minimum_should_match'] = 1
            if filter_clauses:
                bool_query['filter'] = filter_clauses
            query = {'bool': bool_query}
        
        return query
    
    def _build_sort_config(self, sort_by: str, sort_order: str, location: Optional[GeoPoint]) -> List[Dict[str, Any]]:
        """Build sort configuration for OpenSearch query."""
        sort_config = []
        
        if sort_by == "relevance":
            sort_config.append({"_score": {"order": "desc"}})
        elif sort_by == "price":
            sort_config.append({"price": {"order": sort_order}})
        elif sort_by == "beds":
            sort_config.append({"beds": {"order": sort_order}})
        elif sort_by == "baths":
            sort_config.append({"baths": {"order": sort_order}})
        elif sort_by == "date_added":
            sort_config.append({"date_added": {"order": sort_order}})
        elif sort_by == "distance" and location:
            sort_config.append({
                "_geo_distance": {
                    "location": {"lat": location.lat, "lon": location.lon},
                    "order": sort_order,
                    "unit": "km"
                }
            })
        
        # Always add relevance score as secondary sort
        if sort_by != "relevance":
            sort_config.append({"_score": {"order": "desc"}})
        
        # Add ID as final tiebreaker
        sort_config.append({"id": {"order": "asc"}})
        
        return sort_config
    
    def _process_search_hit(self, hit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single search hit into a PropertyListing."""
        try:
            source = hit['_source']
            
            # Build property data
            property_data = {
                'id': source.get('id'),
                'price': source.get('price'),
                'beds': source.get('beds'),
                'baths': source.get('baths'),
                'location': source.get('location'),
                'address': source.get('address'),
                'city': source.get('city'),
                'neighborhood': source.get('neighborhood'),
                'property_type': source.get('property_type'),
                'title': source.get('title'),
                'description': source.get('description'),
                'amenities': source.get('amenities', []),
                'images': source.get('images', []),
                'date_added': source.get('date_added'),
                'date_updated': source.get('date_updated'),
                'score': hit.get('_score'),
            }
            
            # Remove None values
            return {k: v for k, v in property_data.items() if v is not None}
            
        except Exception as e:
            logger.warning(f"Error processing search hit: {e}")
            return None
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        stats = {
            'is_connected': self.is_connected,
            'search_count': self.search_count,
            'error_count': self.error_count,
            'average_query_time': (
                self.total_query_time / self.search_count 
                if self.search_count > 0 else 0
            )
        }
        
        # Get cluster stats if connected
        if await self.health_check():
            try:
                cluster_stats = self.client.cluster.stats()
                stats.update({
                    'cluster_name': cluster_stats.get('cluster_name'),
                    'document_count': 0  # Placeholder
                })
            except Exception as e:
                logger.warning(f"Failed to get OpenSearch stats: {e}")
        
        return stats


# Global OpenSearch client instance
opensearch_client = OpenSearchClient() 