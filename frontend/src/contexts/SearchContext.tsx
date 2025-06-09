import React, { createContext, useContext, ReactNode } from 'react'
import { useSearch } from '../hooks/useSearch'
import { SearchState } from '../types/search'

interface SearchContextType {
  searchState: SearchState
  search: (query: string, limit?: number) => Promise<void>
  clearSearch: () => void
  isLoading: boolean
  results: any[]
  parsedQuery?: any
  total: number
  error?: string
  metrics?: any
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