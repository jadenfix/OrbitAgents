import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { AuthContextType, User, LoginCredentials, RegisterData, ApiError } from '@/types/auth'
import { authAPI, tokenStorage } from '@/services/auth'

interface AuthProviderProps {
  children: ReactNode
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = tokenStorage.getToken()
      
      if (storedToken && !tokenStorage.isTokenExpired()) {
        setToken(storedToken)
        try {
          const userData = await authAPI.getCurrentUser()
          setUser(userData)
        } catch (error) {
          // Token is invalid or user doesn't exist
          logout()
        }
      }
      setIsLoading(false)
    }

    initializeAuth()
  }, [])

  // Set up token expiry checker
  useEffect(() => {
    if (!token) return

    const checkTokenExpiry = () => {
      if (tokenStorage.isTokenExpired()) {
        logout()
      }
    }

    // Check token expiry every minute
    const interval = setInterval(checkTokenExpiry, 60000)
    
    return () => clearInterval(interval)
  }, [token])

  const login = async (credentials: LoginCredentials): Promise<void> => {
    setIsLoading(true)
    try {
      const authResponse = await authAPI.login(credentials)
      setToken(authResponse.access_token)
      
      // Fetch user data
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
    } catch (error: any) {
      const apiError: ApiError = {
        detail: error.response?.data?.detail || 'Login failed',
        status: error.response?.status
      }
      throw apiError
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData): Promise<void> => {
    setIsLoading(true)
    try {
      await authAPI.register(data)
      // After successful registration, log the user in
      await login({ email: data.email, password: data.password })
    } catch (error: any) {
      const apiError: ApiError = {
        detail: error.response?.data?.detail || 'Registration failed',
        status: error.response?.status
      }
      throw apiError
    } finally {
      setIsLoading(false)
    }
  }

  const logout = (): void => {
    authAPI.logout()
    setUser(null)
    setToken(null)
    // Redirect to login page
    window.location.href = '/login'
  }

  const refreshAuth = async (): Promise<void> => {
    try {
      if (token && !tokenStorage.isTokenExpired()) {
        const userData = await authAPI.getCurrentUser()
        setUser(userData)
      }
    } catch (error) {
      logout()
    }
  }

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token && !tokenStorage.isTokenExpired(),
    isLoading,
    login,
    register,
    logout,
    refreshAuth
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
} 