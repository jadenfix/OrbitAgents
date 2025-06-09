import { SearchPipelineRequest, SearchPipelineResponse } from '../types/search'

const API_BASE_URL = (import.meta as any).env?.VITE_QUERY_SERVICE_URL || 'http://localhost:8001'

interface ApiResponse<T> {
  data?: T
  error?: string
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
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      return { data }
    } catch (error) {
      console.error('API request failed:', error)
      return { 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      }
    }
  }

  /**
   * Search for properties using the complete pipeline (parse + search)
   */
  async searchPipeline(request: SearchPipelineRequest): Promise<ApiResponse<SearchPipelineResponse>> {
    return this.makeRequest<SearchPipelineResponse>('/search_pipeline', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  /**
   * Get service health and statistics
   */
  async getHealth(): Promise<ApiResponse<any>> {
    return this.makeRequest<any>('/health')
  }

  /**
   * Get service statistics for monitoring
   */
  async getStats(): Promise<ApiResponse<any>> {
    return this.makeRequest<any>('/stats')
  }
}

export const searchService = new SearchService()
export default searchService 