import { createContext, useContext } from 'react';
import { PropertyListing, ParsedQuery } from '../types/search';

interface SearchContextType {
  query: string;
  results: PropertyListing[];
  parsedQuery?: ParsedQuery;
  total: number;
  isLoading: boolean;
  error?: string;
  metrics?: {
    parse_time_ms: number;
    search_time_ms: number;
    total_time_ms: number;
  };
  search: (query: string) => Promise<void>;
  clearSearch: () => void;
}

export const SearchContext = createContext<SearchContextType | undefined>(
  undefined
);

export const useSearchContext = (): SearchContextType => {
  const context = useContext(SearchContext);
  if (context === undefined) {
    throw new Error('useSearchContext must be used within a SearchProvider');
  }
  return context;
};
