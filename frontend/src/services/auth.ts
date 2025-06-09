import axios, { AxiosResponse } from 'axios'
import { AuthResponse, LoginCredentials, RegisterData, User } from '@/types/auth'

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/auth',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token management
export const tokenStorage = {
  getToken: (): string | null => {
    return localStorage.getItem('auth_token')
  },
  setToken: (token: string): void => {
    localStorage.setItem('auth_token', token)
  },
  removeToken: (): void => {
    localStorage.removeItem('auth_token')
  },
  getTokenExpiry: (): number | null => {
    const expiry = localStorage.getItem('auth_token_expiry')
    return expiry ? parseInt(expiry, 10) : null
  },
  setTokenExpiry: (expiresIn: number): void => {
    const expiryTime = Date.now() + (expiresIn * 1000)
    localStorage.setItem('auth_token_expiry', expiryTime.toString())
  },
  isTokenExpired: (): boolean => {
    const expiry = tokenStorage.getTokenExpiry()
    if (!expiry) return true
    return Date.now() > expiry
  }
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = tokenStorage.getToken()
    if (token && !tokenStorage.isTokenExpired()) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle token expiry
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      tokenStorage.removeToken()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API functions
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response: AxiosResponse<AuthResponse> = await api.post('/login', credentials)
    const { access_token, expires_in } = response.data
    
    // Store token and expiry
    tokenStorage.setToken(access_token)
    tokenStorage.setTokenExpiry(expires_in)
    
    return response.data
  },

  register: async (data: RegisterData): Promise<User> => {
    const response: AxiosResponse<User> = await api.post('/register', data)
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response: AxiosResponse<User> = await api.get('/me')
    return response.data
  },

  logout: (): void => {
    tokenStorage.removeToken()
  },

  // Health check for service availability
  healthCheck: async (): Promise<boolean> => {
    try {
      await api.get('/healthz')
      return true
    } catch {
      return false
    }
  }
}

export default api 