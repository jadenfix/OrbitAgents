export interface ParsedQuery {
  beds?: number
  beds_min?: number
  beds_max?: number
  baths?: number
  baths_min?: number
  baths_max?: number
  city?: string
  neighborhoods: string[]
  max_price?: number
  min_price?: number
  property_type?: 'apartment' | 'house' | 'condo' | 'townhouse' | 'studio' | 'other'
  keywords: string[]
  has_parking?: boolean
  has_pets?: boolean
  has_furnished?: boolean
  confidence: number
}

export interface GeoPoint {
  lat: number
  lon: number
}

export interface PropertyListing {
  id: string
  price: number
  beds: number
  baths: number
  location: GeoPoint
  address: string
  city: string
  neighborhood?: string
  property_type: 'apartment' | 'house' | 'condo' | 'townhouse' | 'studio' | 'other'
  title: string
  description?: string
  amenities: string[]
  images: string[]
  date_added: string
  date_updated?: string
  score?: number
  distance?: number
}

export interface SearchPipelineRequest {
  q: string
  limit?: number
  include_parse_details?: boolean
}

export interface SearchPipelineResponse {
  query: string
  parse?: ParsedQuery
  listings: PropertyListing[]
  total: number
  limit: number
  parse_time_ms: number
  search_time_ms: number
  total_time_ms: number
}

export interface SearchState {
  query: string
  results: PropertyListing[]
  parsedQuery?: ParsedQuery
  total: number
  isLoading: boolean
  error?: string
  metrics?: {
    parse_time_ms: number
    search_time_ms: number
    total_time_ms: number
  }
} 