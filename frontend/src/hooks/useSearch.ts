import { useState, useCallback } from 'react'
import { SearchState, PropertyListing, ParsedQuery } from '../types/search'
import { searchService } from '../services/search'

export const useSearch = () => {
  const [searchState, setSearchState] = useState<SearchState>({
    query: '',
    results: [],
    total: 0,
    isLoading: false,
  })

  const search = useCallback(async (query: string, limit: number = 10) => {
    if (!query.trim()) {
      return
    }

    setSearchState(prev => ({
      ...prev,
      query: query.trim(),
      isLoading: true,
      error: undefined,
    }))

    try {
      const response = await searchService.searchPipeline({
        q: query.trim(),
        limit,
        include_parse_details: true,
      })

      if (response.error) {
        setSearchState(prev => ({
          ...prev,
          isLoading: false,
          error: response.error,
        }))
        return
      }

      if (response.data) {
        setSearchState(prev => ({
          ...prev,
          results: response.data!.listings,
          parsedQuery: response.data!.parse,
          total: response.data!.total,
          isLoading: false,
          metrics: {
            parse_time_ms: response.data!.parse_time_ms,
            search_time_ms: response.data!.search_time_ms,
            total_time_ms: response.data!.total_time_ms,
          },
        }))
      }
    } catch (error) {
      setSearchState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }))
    }
  }, [])

  const clearSearch = useCallback(() => {
    setSearchState({
      query: '',
      results: [],
      total: 0,
      isLoading: false,
    })
  }, [])

  return {
    searchState,
    search,
    clearSearch,
    isLoading: searchState.isLoading,
    results: searchState.results,
    parsedQuery: searchState.parsedQuery,
    total: searchState.total,
    error: searchState.error,
    metrics: searchState.metrics,
  }
} 