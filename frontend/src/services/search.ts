import { SearchPipelineRequest, SearchPipelineResponse } from '../types/search';

const API_BASE_URL = '/api/query';

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class SearchService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          typeof errorData.detail === 'string'
            ? errorData.detail
            : `Search unavailable (HTTP ${response.status}).`
        );
      }

      const data = await response.json();
      return { data };
    } catch (error) {
      return {
        error:
          error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  /**
   * Search for properties using the complete pipeline (parse + search)
   */
  async searchPipeline(
    request: SearchPipelineRequest,
    signal?: AbortSignal
  ): Promise<ApiResponse<SearchPipelineResponse>> {
    const response = await this.makeRequest<SearchPipelineResponse>(
      '/search_pipeline',
      {
        method: 'POST',
        body: JSON.stringify(request),
        signal,
      }
    );
    const data = response.data;
    if (
      data &&
      (!Array.isArray(data.listings) ||
        !Number.isInteger(data.total) ||
        data.total < data.listings.length ||
        ![data.parse_time_ms, data.search_time_ms, data.total_time_ms].every(
          (value) => Number.isFinite(value) && value >= 0
        ) ||
        !data.listings.every(
          (item) =>
            typeof item.id === 'string' &&
            typeof item.title === 'string' &&
            typeof item.address === 'string' &&
            typeof item.city === 'string' &&
            typeof item.date_added === 'string' &&
            Array.isArray(item.amenities) &&
            Array.isArray(item.images) &&
            typeof item.property_type === 'string' &&
            [
              item.price,
              item.beds,
              item.baths,
              item.location?.lat,
              item.location?.lon,
            ].every(Number.isFinite)
        ))
    ) {
      return { error: 'Search service returned invalid listing data.' };
    }
    return response;
  }

  /**
   * Get service health and statistics
   */
  async getHealth(): Promise<ApiResponse<Record<string, unknown>>> {
    return this.makeRequest<Record<string, unknown>>('/health');
  }

  /**
   * Get service statistics for monitoring
   */
  async getStats(): Promise<ApiResponse<Record<string, unknown>>> {
    return this.makeRequest<Record<string, unknown>>('/stats');
  }
}

export const searchService = new SearchService();
export default searchService;
