import React, { ReactNode } from 'react';
import { useSearch } from '../hooks/useSearch';
import { SearchContext } from './useSearchContext';

interface SearchProviderProps {
  children: ReactNode;
}

export const SearchProvider: React.FC<SearchProviderProps> = ({ children }) => {
  const searchHook = useSearch();

  return (
    <SearchContext.Provider value={searchHook}>
      {children}
    </SearchContext.Provider>
  );
};
