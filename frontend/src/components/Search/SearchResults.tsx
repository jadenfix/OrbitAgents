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
      <div className="space-y-4">
        {[...Array(3)].map((_, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-3"></div>
              <div className="h-16 bg-gray-200 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-8">
        <HomeIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No properties found</h3>
        <p className="mt-1 text-sm text-gray-500">
          Try adjusting your search criteria or searching in a different area.
        </p>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Search Results
        </h2>
        <span className="text-sm text-gray-500">
          {results.length} of {total} properties
        </span>
      </div>
      
      <div className="space-y-4">
        {results.map((listing) => (
          <PropertyCard key={listing.id} listing={listing} />
        ))}
      </div>
      
      {results.length < total && (
        <div className="mt-4 text-center">
          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            Load more properties...
          </button>
        </div>
      )}
    </div>
  )
}

export default SearchResults 