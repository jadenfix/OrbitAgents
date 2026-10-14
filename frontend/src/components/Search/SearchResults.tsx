import React from 'react';
import { PropertyListing } from '../../types/search';

interface SearchResultsProps {
  results: PropertyListing[];
  isLoading: boolean;
  total?: number;
  query?: string;
  error?: string;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  isLoading,
  total,
  query,
  error,
}) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatRelevanceScore = (score: number) => {
    return (score * 100).toFixed(1);
  };

  if (isLoading) {
    return (
      <div className="space-y-4 p-6">
        {/* Loading skeletons */}
        {[...Array(3)].map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-lg bg-white p-6 shadow-md"
          >
            <div className="mb-4 h-4 w-3/4 rounded bg-gray-200"></div>
            <div className="mb-2 h-6 w-1/2 rounded bg-gray-200"></div>
            <div className="mb-2 h-4 w-full rounded bg-gray-200"></div>
            <div className="h-4 w-2/3 rounded bg-gray-200"></div>
          </div>
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="p-6">
        <div className="py-12 text-center">
          <div className="mx-auto h-24 w-24 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            {error
              ? 'Search unavailable'
              : query
                ? 'No properties found'
                : 'Start your property search'}
          </h3>
          <p className="mt-2 text-sm text-gray-500">
            {error ||
              (query
                ? 'Try adjusting your search criteria or search for a different area.'
                : 'Enter a city, budget, or bedroom count in the chat. Results come from your configured property index.')}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">
            {results.length} Properties{' '}
            {total && total > results.length ? `of ${total}` : ''}
          </h2>
        </div>

        <div className="space-y-4">
          {results.map((listing) => (
            <div
              key={listing.id}
              className="rounded-lg border border-gray-200 bg-white p-6 shadow-md transition-shadow hover:shadow-lg"
            >
              {/* Header */}
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="mb-1 text-lg font-semibold text-gray-900">
                    {listing.title ||
                      `${listing.beds} bed, ${listing.baths} bath ${listing.property_type}`}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {listing.address}, {listing.city}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-600">
                    {formatPrice(listing.price)}
                  </div>
                  {listing.score && (
                    <div className="text-xs text-gray-500">
                      {formatRelevanceScore(listing.score)}% match
                    </div>
                  )}
                </div>
              </div>

              {/* Property Details */}
              <div className="mb-4 grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {listing.beds}
                  </div>
                  <div className="text-sm text-gray-500">Bedrooms</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-900">
                    {listing.baths}
                  </div>
                  <div className="text-sm text-gray-500">Bathrooms</div>
                </div>
              </div>

              {/* Property Type */}
              <div className="mb-4">
                <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
                  {listing.property_type}
                </span>
              </div>

              {/* Amenities */}
              {listing.amenities && listing.amenities.length > 0 && (
                <div className="mb-4">
                  <h4 className="mb-2 text-sm font-medium text-gray-900">
                    Amenities
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {listing.amenities.slice(0, 6).map((amenity, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center rounded-md bg-blue-100 px-2 py-1 text-xs font-medium text-blue-800"
                      >
                        {amenity}
                      </span>
                    ))}
                    {listing.amenities.length > 6 && (
                      <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600">
                        +{listing.amenities.length - 6} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Additional Info */}
              <div className="space-y-1 text-sm text-gray-500">
                <div>
                  <span className="font-medium">Listed:</span>{' '}
                  {new Date(listing.date_added).toLocaleDateString()}
                </div>
                {listing.score && (
                  <div>
                    <span className="font-medium">Relevance:</span>{' '}
                    {formatRelevanceScore(listing.score)}%
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SearchResults;
