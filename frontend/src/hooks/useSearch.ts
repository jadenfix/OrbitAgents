import { useEffect, useRef, useState } from 'react';
import { SearchState } from '../types/search';
import { searchService } from '../services/search';

const emptyState: SearchState = {
  query: '',
  results: [],
  total: 0,
  isLoading: false,
};

export const useSearch = () => {
  const [searchState, setSearchState] = useState<SearchState>(emptyState);
  const requestId = useRef(0);
  const controller = useRef<AbortController>();
  useEffect(() => () => controller.current?.abort(), []);

  const search = async (query: string) => {
    const q = query.trim();
    if (!q || q.length > 500)
      throw new Error('Enter a search between 1 and 500 characters.');
    controller.current?.abort();
    controller.current = new AbortController();
    const id = ++requestId.current;
    setSearchState({ ...emptyState, query: q, isLoading: true });
    const activeController = controller.current;
    const timeout = window.setTimeout(() => activeController.abort(), 20000);
    let response;
    try {
      response = await searchService.searchPipeline(
        { q, limit: 20, include_parse_details: true },
        activeController.signal
      );
    } finally {
      window.clearTimeout(timeout);
    }
    if (id !== requestId.current)
      throw new Error('Search replaced by a newer request.');
    if (!response.data || response.error) {
      const error = response.error || 'Search service returned no data.';
      setSearchState({ ...emptyState, query: q, error });
      throw new Error(error);
    }
    const data = response.data;
    setSearchState({
      query: q,
      results: data.listings,
      total: data.total,
      parsedQuery: data.parse,
      isLoading: false,
      metrics: {
        parse_time_ms: data.parse_time_ms,
        search_time_ms: data.search_time_ms,
        total_time_ms: data.total_time_ms,
      },
    });
    return data;
  };

  const clearSearch = () => {
    ++requestId.current;
    controller.current?.abort();
    setSearchState(emptyState);
  };
  return { ...searchState, search, clearSearch };
};
