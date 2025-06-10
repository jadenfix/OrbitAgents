import React from 'react'
import { PropertyListing } from '../../types/search'
import { 
  HomeIcon, 
  MapPinIcon, 
  CurrencyDollarIcon,
  BuildingOfficeIcon 
} from '@heroicons/react/24/outline'

interface SearchResultsProps {
  results: PropertyListing[]
  total: number
  isLoading: boolean
  error?: string
}

const PropertyCard: React.FC<{ listing: PropertyListing }> = ({ listing }) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price)
  }

  const formatPropertyType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1)
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
          {listing.title}
        </h3>
        <span className="text-xl font-bold text-green-600">
          {formatPrice(listing.price)}
        </span>
      </div>
      
      <div className="flex items-center text-gray-600 mb-2">
        <MapPinIcon className="w-4 h-4 mr-1" />
        <span className="text-sm">{listing.address}, {listing.city}</span>
      </div>
      
      <div className="flex items-center justify-between text-sm text-gray-700 mb-3">
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <HomeIcon className="w-4 h-4 mr-1" />
            <span>{listing.beds} bed{listing.beds !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center">
            <BuildingOfficeIcon className="w-4 h-4 mr-1" />
            <span>{listing.baths} bath{listing.baths !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center">
            <CurrencyDollarIcon className="w-4 h-4 mr-1" />
            <span>{formatPropertyType(listing.property_type)}</span>
          </div>
        </div>
        
        {listing.distance && (
          <span className="text-xs text-gray-500">
            {listing.distance.toFixed(1)} km away
          </span>
        )}
      </div>
      
      {listing.description && (
        <p className="text-sm text-gray-600 line-clamp-2 mb-3">
          {listing.description}
        </p>
      )}
      
      {listing.amenities.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {listing.amenities.slice(0, 3).map((amenity, index) => (
            <span
              key={index}
              className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
            >
              {amenity}
            </span>
          ))}
          {listing.amenities.length > 3 && (
            <span className="text-xs text-gray-500">
              +{listing.amenities.length - 3} more
            </span>
          )}
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>
          Added {new Date(listing.date_added).toLocaleDateString()}
        </span>
        {listing.score && (
          <span>
            Relevance: {Math.round(listing.score * 100)}%
          </span>
        )}
      </div>
    </div>
  )
}

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  total,
  isLoading,
  error
}) => {
  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex">
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              Search Error
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        {/* Loading skeletons */}
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
            <div className="flex justify-between items-start mb-4">
              <div className="h-6 bg-gray-200 rounded w-3/4"></div>
              <div className="h-6 bg-gray-200 rounded w-20"></div>
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
          <p className="text-gray-600">Try adjusting your search criteria or filters</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 space-y-4 overflow-y-auto h-full">
      <div className="text-sm text-gray-600 mb-4">
        {results.length} properties found
      </div>
      
      {results.map((listing, index) => (
        <div key={index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
          {/* Header */}
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-bold text-gray-900 leading-tight">
              {listing.title}
            </h3>
            <div className="text-right">
              <div className="text-xl font-bold text-green-600">
                {formatPrice(listing.price)}
              </div>
                             {listing.relevance_score && (
                 <div className="text-xs text-gray-500">
                   {formatRelevanceScore(listing.relevance_score)}% match
                 </div>
               )}
            </div>
          </div>

          {/* Property Details */}
          <div className="flex flex-wrap gap-2 mb-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {listing.beds} bed
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {listing.baths} bath
            </span>
                         <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
               {listing.property_type}
             </span>
          </div>

          {/* Address */}
          <div className="text-sm text-gray-600 mb-3">
            📍 {listing.address}
          </div>

          {/* Amenities */}
          {listing.amenities && listing.amenities.length > 0 && (
            <div className="mb-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Amenities</h4>
              <div className="flex flex-wrap gap-1">
                {listing.amenities.slice(0, 6).map((amenity, idx) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-700"
                  >
                    {amenity}
                  </span>
                ))}
                {listing.amenities.length > 6 && (
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-500">
                    +{listing.amenities.length - 6} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          {listing.performance_metrics && (
            <div className="mt-4 pt-3 border-t border-gray-200">
              <div className="grid grid-cols-2 gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-medium">Query Time:</span> {listing.performance_metrics.query_time_ms}ms
                </div>
                                 <div>
                   <span className="font-medium">Relevance:</span> {formatRelevanceScore(listing.relevance_score || 0)}%
                 </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-4 flex gap-2">
            <button className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
              View Details
            </button>
            <button className="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-200 transition-colors">
              Save Property
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default SearchResults 