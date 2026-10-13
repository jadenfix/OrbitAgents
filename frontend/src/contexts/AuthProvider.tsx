import { isAxiosError } from 'axios';
import React, { useEffect, useState, ReactNode } from 'react';
import {
  AuthContextType,
  User,
  LoginCredentials,
  RegisterData,
  ApiError,
} from '@/types/auth';
import { authAPI, tokenStorage } from '@/services/auth';
import { AuthContext } from './AuthContext';

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = tokenStorage.getToken();

      if (storedToken && !tokenStorage.isTokenExpired()) {
        setToken(storedToken);
        try {
          const userData = await authAPI.getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token is invalid or user doesn't exist
          logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  // Set up token expiry checker
  useEffect(() => {
    if (!token) return;

    const checkTokenExpiry = () => {
      if (tokenStorage.isTokenExpired()) {
        logout();
      }
    };

    // Check token expiry every minute
    const interval = setInterval(checkTokenExpiry, 60000);

    return () => clearInterval(interval);
  }, [token]);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const authResponse = await authAPI.login(credentials);
      setToken(authResponse.access_token);

      // Fetch user data
      const userData = await authAPI.getCurrentUser();
      setUser(userData);
    } catch (error: unknown) {
      const apiError: ApiError = {
        detail: isAxiosError(error)
          ? error.response?.data?.detail || 'Login failed'
          : 'Login failed',
        status: isAxiosError(error) ? error.response?.status : undefined,
      };
      throw apiError;
    }
  };

  const register = async (data: RegisterData): Promise<void> => {
    try {
      await authAPI.register(data);
      // After successful registration, log the user in
      await login({ email: data.email, password: data.password });
    } catch (error: unknown) {
      const apiError: ApiError = {
        detail: isAxiosError(error)
          ? error.response?.data?.detail || 'Registration failed'
          : 'Registration failed',
        status: isAxiosError(error) ? error.response?.status : undefined,
      };
      throw apiError;
    }
  };

  const logout = (): void => {
    authAPI.logout();
    setUser(null);
    setToken(null);
    // Redirect to login page
    window.location.href = '/login';
  };

  const refreshAuth = async (): Promise<void> => {
    try {
      if (token && !tokenStorage.isTokenExpired()) {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token && !tokenStorage.isTokenExpired(),
    isLoading,
    login,
    register,
    logout,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
