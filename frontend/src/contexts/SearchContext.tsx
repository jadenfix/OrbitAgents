import React, { createContext, useContext, ReactNode } from 'react'
import { useSearch } from '../hooks/useSearch'
import { PropertyListing, ParsedQuery } from '../types/search'

interface SearchContextType {
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
  search: (query: string) => Promise<void>
  clearSearch: () => void
}

const SearchContext = createContext<SearchContextType | undefined>(undefined)

interface SearchProviderProps {
  children: ReactNode
}

export const SearchProvider: React.FC<SearchProviderProps> = ({ children }) => {
  const searchHook = useSearch()

  return (
    <SearchContext.Provider value={searchHook}>
      {children}
    </SearchContext.Provider>
  )
}

export const useSearchContext = (): SearchContextType => {
  const context = useContext(SearchContext)
  if (context === undefined) {
    throw new Error('useSearchContext must be used within a SearchProvider')
  }
  return context
} 