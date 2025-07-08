import { useState } from 'react'
import { SearchState } from '../types/search'

export const useSearch = () => {
  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    results: [],
    total: 0,
    isLoading: false,
  })

  const search = async (query: string) => {
    setSearchState(prev => ({
      ...prev,
      isLoading: true,
      error: undefined,
      query,
    }))

    try {
      // Simulated API call - replace with actual implementation
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Mock results for demonstration
      const mockResults = [
        {
          id: '1',
          title: 'Beautiful 2BR Apartment',
          address: '123 Main St',
          city: 'Denver',
          price: 2500,
          beds: 2,
          baths: 2,
          property_type: 'apartment' as const,
          amenities: ['Parking', 'Pool'],
          images: ['https://example.com/image1.jpg'],
          date_added: new Date().toISOString(),
          location: { lat: 39.7392, lon: -104.9903 }
        }
      ]

      setSearchState(prev => ({
        ...prev,
        results: mockResults,
        total: mockResults.length,
        isLoading: false,
      }))
    } catch (error) {
      setSearchState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Search failed',
        isLoading: false,
      }))
    }
  }

  const clearSearch = () => {
    setSearchState({
      query: '',
      results: [],
      total: 0,
      isLoading: false,
    })
  }

  return {
    ...searchState,
    search,
    clearSearch,
  }
} 